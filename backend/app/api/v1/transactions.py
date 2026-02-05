from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.account import Account
from app.models.transaction import Transaction, TransactionStatus
from app.models.user import User
from app.schemas.transaction import TransactionResponse
from app.services.soft_delete import SoftDeleteService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=List[TransactionResponse])
def get_transaction_history(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    status: Optional[TransactionStatus] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get transaction history for the current user with optional filters."""
    user_account_ids = db.query(Account.id).filter(Account.user_id == current_user.id)

    base_query = db.query(Transaction).filter(
        or_(
            Transaction.from_account_id.in_(user_account_ids),
            Transaction.to_account_id.in_(user_account_ids),
        )
    )
    query = SoftDeleteService.get_active_query(base_query, Transaction)

    if account_id:
        account = (
            db.query(Account)
            .filter(
                Account.id == account_id,
                Account.user_id == current_user.id,
            )
            .first()
        )
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        query = query.filter(
            or_(
                Transaction.from_account_id == account_id,
                Transaction.to_account_id == account_id,
            )
        )

    if status:
        query = query.filter(Transaction.status == status)
    if start_date:
        query = query.filter(Transaction.created_at >= start_date)
    if end_date:
        query = query.filter(Transaction.created_at <= end_date)

    query = query.order_by(Transaction.created_at.desc())
    offset = (page - 1) * page_size
    transactions = query.offset(offset).limit(page_size).all()
    return transactions
