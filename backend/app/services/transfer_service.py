from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from contextlib import contextmanager
from fastapi import HTTPException, status, Request
from decimal import Decimal
from typing import Optional
import logging
from app.models.account import Account
from app.models.transaction import Transaction, TransactionStatus
from app.schemas.transaction import TransferCreate
from app.services.account_service import AccountService
from app.services.fraud_service import FraudService
from app.services.ledger_service import LedgerService
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


@contextmanager
def transaction_context(db: Session):
    """Context manager for atomic database transactions"""
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction rolled back: {str(e)}")
        raise


class TransferService:
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    @staticmethod
    def transfer_money(
        db: Session,
        from_user_id: int,
        transfer_data: TransferCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Transaction:
        """
        Transfer money between accounts with production-level features:
        - SELECT FOR UPDATE for atomicity
        - Fraud checks
        - Double-entry ledger
        - Audit logging
        - Failure handling with retries
        """
        # Validate currency
        AccountService.validate_currency(transfer_data.currency)
        
        # Fraud checks
        fraud_check = FraudService.check_transfer_limits(
            db=db,
            user_id=from_user_id,
            amount=transfer_data.amount,
            ip_address=ip_address,
            request_id=request_id
        )
        
        if not fraud_check.get("allowed", False):
            AuditService.log_transfer(
                db=db,
                transaction_id=0,  # No transaction yet
                user_id=from_user_id,
                from_account_id=transfer_data.from_account_id,
                to_account_id=transfer_data.to_account_id,
                amount=float(transfer_data.amount),
                currency=transfer_data.currency,
                status="blocked",
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                error_message=fraud_check.get("reason", "Fraud check failed")
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=fraud_check.get("reason", "Transfer blocked by fraud detection")
            )
        
        # Retry logic for transient failures
        last_exception = None
        for attempt in range(TransferService.MAX_RETRIES):
            try:
                return TransferService._execute_transfer(
                    db=db,
                    from_user_id=from_user_id,
                    transfer_data=transfer_data,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                    attempt=attempt + 1
                )
            except (OperationalError, IntegrityError) as e:
                last_exception = e
                if attempt < TransferService.MAX_RETRIES - 1:
                    logger.warning(f"Transfer attempt {attempt + 1} failed, retrying: {str(e)}")
                    import time
                    time.sleep(TransferService.RETRY_DELAY * (attempt + 1))
                    continue
                else:
                    logger.error(f"Transfer failed after {TransferService.MAX_RETRIES} attempts: {str(e)}")
                    raise
            except Exception as e:
                # Non-retryable errors
                logger.error(f"Transfer failed with non-retryable error: {str(e)}")
                raise
        
        # Should not reach here, but handle it
        if last_exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Transfer failed after multiple retry attempts"
            )

    @staticmethod
    def _execute_transfer(
        db: Session,
        from_user_id: int,
        transfer_data: TransferCreate,
        ip_address: Optional[str],
        user_agent: Optional[str],
        request_id: Optional[str],
        attempt: int
    ) -> Transaction:
        """Execute the actual transfer with full atomicity"""
        
        with transaction_context(db):
            # Get and lock the source account (SELECT FOR UPDATE)
            from_account = db.query(Account).with_for_update().filter(
                Account.id == transfer_data.from_account_id,
                Account.user_id == from_user_id,
                Account.is_deleted == False
            ).first()

            if not from_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Source account not found or does not belong to user"
                )

            # Get and lock the destination account (SELECT FOR UPDATE)
            to_account = db.query(Account).with_for_update().filter(
                Account.id == transfer_data.to_account_id,
                Account.is_deleted == False
            ).first()

            if not to_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Destination account not found"
                )

            # Validate accounts are different
            if from_account.id == to_account.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot transfer to the same account"
                )

            # Validate currencies match
            if from_account.currency != transfer_data.currency.upper():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Currency mismatch. Source account currency: {from_account.currency}, Transfer currency: {transfer_data.currency.upper()}"
                )

            if to_account.currency != transfer_data.currency.upper():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Currency mismatch. Destination account currency: {to_account.currency}, Transfer currency: {transfer_data.currency.upper()}"
                )

            # Validate sufficient balance (double-check after lock)
            if from_account.balance < transfer_data.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient balance. Available: {from_account.balance}, Required: {transfer_data.amount}"
                )

            # Store balances before transfer for ledger
            from_balance_before = from_account.balance
            to_balance_before = to_account.balance

            # Create transaction record
            transaction = Transaction(
                from_account_id=from_account.id,
                to_account_id=to_account.id,
                amount=transfer_data.amount,
                currency=transfer_data.currency.upper(),
                status=TransactionStatus.PENDING,
                retry_count=attempt - 1
            )
            db.add(transaction)
            db.flush()  # Get transaction ID

            try:
                # Perform the transfer atomically
                from_account.balance -= transfer_data.amount
                to_account.balance += transfer_data.amount
                transaction.status = TransactionStatus.COMPLETED

                # Create ledger entries (double-entry bookkeeping)
                LedgerService.create_ledger_entries(
                    db=db,
                    transaction=transaction,
                    from_account=from_account,
                    to_account=to_account,
                    amount=transfer_data.amount
                )

                # Audit log
                AuditService.log_transfer(
                    db=db,
                    transaction_id=transaction.id,
                    user_id=from_user_id,
                    from_account_id=from_account.id,
                    to_account_id=to_account.id,
                    amount=float(transfer_data.amount),
                    currency=transfer_data.currency,
                    status="success",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id
                )

                db.refresh(transaction)
                return transaction

            except Exception as e:
                # Rollback account balances
                from_account.balance = from_balance_before
                to_account.balance = to_balance_before
                transaction.status = TransactionStatus.FAILED
                transaction.failure_reason = str(e)
                
                # Audit log failure
                AuditService.log_transfer(
                    db=db,
                    transaction_id=transaction.id,
                    user_id=from_user_id,
                    from_account_id=from_account.id,
                    to_account_id=to_account.id,
                    amount=float(transfer_data.amount),
                    currency=transfer_data.currency,
                    status="failed",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                    error_message=str(e)
                )
                
                raise
