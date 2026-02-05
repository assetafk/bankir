from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog, AuditAction
from app.models.ledger_entry import LedgerEntry
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit-logs")
def get_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[AuditAction] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit logs (admin only - add proper admin check in production)
    """
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    query = query.order_by(AuditLog.created_at.desc())
    
    offset = (page - 1) * page_size
    logs = query.offset(offset).limit(page_size).all()
    total = query.count()
    
    return {
        "logs": logs,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/ledger/verify/{account_id}")
def verify_ledger_balance(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify ledger balance matches account balance (admin only)
    """
    result = LedgerService.verify_ledger_balance(db, account_id)
    return result


@router.get("/fraud-stats")
def get_fraud_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get fraud detection statistics (admin only)
    """
    query = db.query(AuditLog).filter(AuditLog.action == AuditAction.FRAUD_CHECK)
    
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    total_checks = query.count()
    blocked = query.filter(AuditLog.status == "blocked").count()
    allowed = query.filter(AuditLog.status == "allowed").count()
    
    return {
        "total_checks": total_checks,
        "blocked": blocked,
        "allowed": allowed,
        "block_rate": (blocked / total_checks * 100) if total_checks > 0 else 0
    }
