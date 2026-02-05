from decimal import Decimal
import logging
from typing import Any, Dict

from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.ledger_entry import LedgerEntry, LedgerEntryType
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class LedgerService:
    """
    Double-entry bookkeeping service
    Every transaction creates two ledger entries: debit and credit
    """
    
    @staticmethod
    def create_ledger_entries(
        db: Session,
        transaction: Transaction,
        from_account: Account,
        to_account: Account,
        amount: Decimal
    ) -> tuple[LedgerEntry, LedgerEntry]:
        """
        Create double-entry ledger entries for a transaction
        Returns (debit_entry, credit_entry)
        """
        try:
            # Debit entry (money leaving from_account)
            debit_entry = LedgerEntry(
                transaction_id=transaction.id,
                account_id=from_account.id,
                entry_type=LedgerEntryType.DEBIT,
                amount=amount,
                currency=transaction.currency,
                balance_before=from_account.balance + amount,  # Before the transfer
                balance_after=from_account.balance  # After the transfer
            )
            
            # Credit entry (money entering to_account)
            credit_entry = LedgerEntry(
                transaction_id=transaction.id,
                account_id=to_account.id,
                entry_type=LedgerEntryType.CREDIT,
                amount=amount,
                currency=transaction.currency,
                balance_before=to_account.balance - amount,  # Before the transfer
                balance_after=to_account.balance  # After the transfer
            )
            
            db.add(debit_entry)
            db.add(credit_entry)
            db.flush()  # Flush to get IDs but don't commit (let transaction context handle it)
            
            return debit_entry, credit_entry
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Failed to create ledger entries: {str(e)}")
            raise

    @staticmethod
    def verify_ledger_balance(db: Session, account_id: int) -> Dict[str, Any]:
        """
        Verify ledger balance matches account balance
        Returns verification result
        """
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return {"valid": False, "error": "Account not found"}
        
        # Calculate balance from ledger entries
        debits = db.query(func.sum(LedgerEntry.amount)).filter(
            and_(
                LedgerEntry.account_id == account_id,
                LedgerEntry.entry_type == LedgerEntryType.DEBIT
            )
        ).scalar() or Decimal("0.00")
        
        credits = db.query(func.sum(LedgerEntry.amount)).filter(
            and_(
                LedgerEntry.account_id == account_id,
                LedgerEntry.entry_type == LedgerEntryType.CREDIT
            )
        ).scalar() or Decimal("0.00")
        
        # Ledger balance = credits - debits
        ledger_balance = credits - debits
        
        # Compare with account balance
        balance_match = abs(account.balance - ledger_balance) < Decimal("0.01")  # Allow small rounding differences
        
        return {
            "valid": balance_match,
            "account_balance": float(account.balance),
            "ledger_balance": float(ledger_balance),
            "difference": float(abs(account.balance - ledger_balance)),
            "debits": float(debits),
            "credits": float(credits)
        }
