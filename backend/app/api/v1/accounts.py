from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.account import AccountCreate, AccountResponse
from app.services.account_service import AccountService
from app.services.audit_service import AuditAction, AuditService
from app.services.soft_delete import SoftDeleteService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: AccountCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new account for the current user"""
    account = AccountService.create_account(db, current_user.id, account_data)

    # Audit log
    AuditService.log_action(
        db=db,
        action=AuditAction.CREATE,
        resource_type="account",
        resource_id=account.id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        request_id=getattr(request.state, "request_id", None),
        details={
            "currency": account.currency,
            "initial_balance": float(account.balance),
        },
    )

    return account


@router.get("", response_model=List[AccountResponse])
def get_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all accounts for the current user"""
    accounts = AccountService.get_user_accounts(db, current_user.id)
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific account by ID"""
    account = AccountService.get_account_by_id(db, account_id, current_user.id)
    return account
