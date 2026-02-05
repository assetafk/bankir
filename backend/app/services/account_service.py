from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal
from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountCreate
from app.services.soft_delete import SoftDeleteService
from app.services.audit_service import AuditService


class AccountService:
    # Valid ISO 4217 currency codes (common ones)
    VALID_CURRENCIES = {
        "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY",
        "INR", "RUB", "BRL", "ZAR", "MXN", "SGD", "HKD", "NOK",
        "SEK", "DKK", "PLN", "TRY", "NZD", "KRW", "THB", "IDR"
    }

    @staticmethod
    def validate_currency(currency: str) -> None:
        """Validate currency code"""
        currency_upper = currency.upper()
        if currency_upper not in AccountService.VALID_CURRENCIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid currency code: {currency}. Supported currencies: {', '.join(sorted(AccountService.VALID_CURRENCIES))}"
            )

    @staticmethod
    def create_account(
        db: Session,
        user_id: int,
        account_data: AccountCreate
    ) -> Account:
        """Create a new account for a user"""
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Validate currency
        AccountService.validate_currency(account_data.currency)

        # Create account (multiple accounts per currency per user are allowed)
        account = Account(
            user_id=user_id,
            currency=account_data.currency.upper(),
            balance=account_data.initial_balance or Decimal("0.00")
        )

        db.add(account)
        db.commit()
        db.refresh(account)

        return account

    @staticmethod
    def get_user_accounts(db: Session, user_id: int) -> list[Account]:
        """Get all active accounts for a user"""
        query = db.query(Account).filter(Account.user_id == user_id)
        return SoftDeleteService.get_active_query(query, Account).all()

    @staticmethod
    def get_account_by_id(db: Session, account_id: int, user_id: int) -> Account:
        """Get account by ID, ensuring it belongs to the user and is not deleted"""
        query = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == user_id
        )
        account = SoftDeleteService.get_active_query(query, Account).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        return account
