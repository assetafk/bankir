from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.models.audit_log import AuditLog, AuditAction
from app.core.request_id import RequestIDMiddleware


class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        action: AuditAction,
        resource_type: str,
        user_id: Optional[int] = None,
        resource_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log an audit event"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            details=details,
            status=status,
            error_message=error_message
        )
        
        db.add(audit_log)
        db.flush()  # Flush to get ID but don't commit (let transaction context handle it)
        db.refresh(audit_log)
        
        return audit_log

    @staticmethod
    def log_transfer(
        db: Session,
        transaction_id: int,
        user_id: int,
        from_account_id: int,
        to_account_id: int,
        amount: float,
        currency: str,
        status: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log a transfer operation"""
        return AuditService.log_action(
            db=db,
            action=AuditAction.TRANSFER,
            resource_type="transaction",
            resource_id=transaction_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            details={
                "from_account_id": from_account_id,
                "to_account_id": to_account_id,
                "amount": float(amount),
                "currency": currency
            },
            status=status,
            error_message=error_message
        )

    @staticmethod
    def log_fraud_check(
        db: Session,
        user_id: int,
        check_type: str,
        result: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """Log a fraud check"""
        return AuditService.log_action(
            db=db,
            action=AuditAction.FRAUD_CHECK,
            resource_type="fraud_check",
            user_id=user_id,
            ip_address=ip_address,
            request_id=request_id,
            details={
                "check_type": check_type,
                "result": result,
                **details
            },
            status=result
        )
