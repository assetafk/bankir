import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.transaction import TransactionResponse, TransferCreate
from app.services.idempotency import IdempotencyService
from app.services.transfer_service import TransferService

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def transfer_money(
    transfer_data: TransferCreate,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Transfer money between accounts.
    Requires Idempotency-Key header to prevent duplicate transfers.
    """
    # Use idempotency key from header or request body
    key = idempotency_key or transfer_data.idempotency_key

    # Validate idempotency key
    IdempotencyService.validate_key(key)

    # Get request metadata for audit and fraud checks
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    request_id = getattr(request.state, "request_id", None)

    # Check for cached response (double request protection)
    if key:
        try:
            cached_response = IdempotencyService.check_key(
                current_user.id,
                key
            )
            if cached_response:
                # Return cached response
                return TransactionResponse(**cached_response)

            # Mark request as processing to prevent duplicate concurrent requests
            IdempotencyService.mark_processing(current_user.id, key)
        except HTTPException:
            raise
        except Exception as e:
            logging.warning("Idempotency check failed: %s", e)

    try:
        # Perform the transfer with all production features
        transaction = TransferService.transfer_money(
            db=db,
            from_user_id=current_user.id,
            transfer_data=transfer_data,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

        # Convert to response model
        response_data = TransactionResponse.model_validate(transaction)

        # Store response for idempotency if key provided
        if key:
            IdempotencyService.store_response(
                current_user.id,
                key,
                response_data.model_dump(),
            )
            IdempotencyService.clear_processing(current_user.id, key)

        return response_data

    except Exception:
        # Clear processing flag on error
        if key:
            IdempotencyService.clear_processing(current_user.id, key)
        raise
