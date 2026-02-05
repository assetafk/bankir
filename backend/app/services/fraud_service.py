from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text, bindparam
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.models.transaction import Transaction, TransactionStatus
from app.models.account import Account
from app.core.redis_client import redis_client
from app.services.audit_service import AuditService
from app.services.soft_delete import SoftDeleteService


class FraudService:
    # Fraud detection thresholds
    MAX_TRANSFER_AMOUNT = Decimal("1000000.00")  # $1M per transaction
    MAX_DAILY_AMOUNT = Decimal("5000000.00")  # $5M per day per user
    MAX_HOURLY_TRANSACTIONS = 50  # Max transactions per hour
    MAX_DAILY_TRANSACTIONS = 200  # Max transactions per day
    MIN_TRANSFER_AMOUNT = Decimal("0.01")  # Minimum transfer amount
    
    @staticmethod
    def check_transfer_limits(
        db: Session,
        user_id: int,
        amount: Decimal,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if transfer violates fraud detection rules
        Returns dict with 'allowed' boolean and 'reason' if blocked
        """
        checks = {
            "amount_check": FraudService._check_amount_limits(amount),
            "daily_amount": FraudService._check_daily_amount(db, user_id, amount),
            "transaction_frequency": FraudService._check_transaction_frequency(db, user_id),
            "ip_check": FraudService._check_ip_limits(ip_address) if ip_address else {"allowed": True}
        }
        
        # Check if any check failed
        for check_name, check_result in checks.items():
            if not check_result.get("allowed", True):
                # Log fraud attempt
                AuditService.log_fraud_check(
                    db=db,
                    user_id=user_id,
                    check_type=check_name,
                    result="blocked",
                    details={
                        "amount": float(amount),
                        "reason": check_result.get("reason", "Unknown")
                    },
                    ip_address=ip_address,
                    request_id=request_id
                )
                return {
                    "allowed": False,
                    "reason": check_result.get("reason", "Fraud check failed"),
                    "check": check_name
                }
        
        # All checks passed
        return {"allowed": True}

    @staticmethod
    def _check_amount_limits(amount: Decimal) -> Dict[str, Any]:
        """Check if amount is within allowed limits"""
        if amount < FraudService.MIN_TRANSFER_AMOUNT:
            return {
                "allowed": False,
                "reason": f"Amount too small. Minimum: {FraudService.MIN_TRANSFER_AMOUNT}"
            }
        
        if amount > FraudService.MAX_TRANSFER_AMOUNT:
            return {
                "allowed": False,
                "reason": f"Amount exceeds maximum transfer limit: {FraudService.MAX_TRANSFER_AMOUNT}"
            }
        
        return {"allowed": True}

    @staticmethod
    def _check_daily_amount(db: Session, user_id: int, new_amount: Decimal) -> Dict[str, Any]:
        """Check daily transfer amount limit (raw SQL to avoid enum/param binding issues)."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        account_ids = [r[0] for r in db.query(Account.id).filter(Account.user_id == user_id).all()]
        if not account_ids:
            return {"allowed": True}

        # Raw SQL with IN (expanding list to separate params to avoid driver/array binding 9h9h)
        stmt = text("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE from_account_id IN :account_ids
              AND status = CAST(:status AS public.transactionstatus)
              AND created_at >= :today_start
              AND is_deleted = false
        """).bindparams(bindparam("account_ids", expanding=True))
        r = db.execute(stmt, {
            "account_ids": account_ids,
            "status": "completed",  # DB enum is lowercase
            "today_start": today_start,
        })
        row = r.fetchone()
        today_total = Decimal(str(row[0])) if row and row[0] is not None else Decimal("0.00")

        if today_total + new_amount > FraudService.MAX_DAILY_AMOUNT:
            return {
                "allowed": False,
                "reason": f"Daily transfer limit exceeded. Today: {today_total}, Limit: {FraudService.MAX_DAILY_AMOUNT}"
            }
        
        return {"allowed": True}

    @staticmethod
    def _check_transaction_frequency(db: Session, user_id: int) -> Dict[str, Any]:
        """Check transaction frequency limits"""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        account_ids = [r[0] for r in db.query(Account.id).filter(Account.user_id == user_id).all()]
        if not account_ids:
            return {"allowed": True}

        # Count transactions in last hour (exclude soft-deleted)
        hourly_query = db.query(func.count(Transaction.id)).filter(
            and_(
                Transaction.from_account_id.in_(account_ids),
                Transaction.created_at >= one_hour_ago
            )
        )
        hourly_query = SoftDeleteService.get_active_query(hourly_query, Transaction)
        hourly_count = hourly_query.scalar() or 0

        # Count transactions today (exclude soft-deleted)
        daily_query = db.query(func.count(Transaction.id)).filter(
            and_(
                Transaction.from_account_id.in_(account_ids),
                Transaction.created_at >= today_start
            )
        )
        daily_query = SoftDeleteService.get_active_query(daily_query, Transaction)
        daily_count = daily_query.scalar() or 0
        
        if hourly_count >= FraudService.MAX_HOURLY_TRANSACTIONS:
            return {
                "allowed": False,
                "reason": f"Too many transactions in the last hour. Limit: {FraudService.MAX_HOURLY_TRANSACTIONS}"
            }
        
        if daily_count >= FraudService.MAX_DAILY_TRANSACTIONS:
            return {
                "allowed": False,
                "reason": f"Too many transactions today. Limit: {FraudService.MAX_DAILY_TRANSACTIONS}"
            }
        
        return {"allowed": True}

    @staticmethod
    def _check_ip_limits(ip_address: str) -> Dict[str, Any]:
        """Check IP-based rate limiting using Redis"""
        if not ip_address:
            return {"allowed": True}
        
        # Check IP rate limit (10 transfers per minute per IP)
        ip_key = f"fraud:ip:{ip_address}"
        current_count = redis_client.get(ip_key)
        
        if current_count and int(current_count) >= 10:
            return {
                "allowed": False,
                "reason": "Too many requests from this IP address. Please try again later."
            }
        
        # Increment counter
        redis_client.set(ip_key, str(int(current_count or 0) + 1), ttl=60)  # 1 minute TTL
        
        return {"allowed": True}
