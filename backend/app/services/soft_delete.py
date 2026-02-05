from sqlalchemy.orm import Session
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from typing import Type, TypeVar, Generic
from fastapi import HTTPException, status

T = TypeVar('T')


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class SoftDeleteService:
    @staticmethod
    def soft_delete(db: Session, model_instance, user_id: int = None) -> None:
        """Soft delete an entity"""
        if hasattr(model_instance, 'is_deleted'):
            model_instance.is_deleted = True
            model_instance.deleted_at = datetime.utcnow()
            db.commit()
        else:
            raise ValueError("Model does not support soft delete")

    @staticmethod
    def restore(db: Session, model_instance) -> None:
        """Restore a soft-deleted entity"""
        if hasattr(model_instance, 'is_deleted'):
            model_instance.is_deleted = False
            model_instance.deleted_at = None
            db.commit()
        else:
            raise ValueError("Model does not support soft delete")

    @staticmethod
    def get_active_query(query, model_class):
        """Filter out soft-deleted records"""
        if hasattr(model_class, 'is_deleted'):
            return query.filter(model_class.is_deleted == False)
        return query

    @staticmethod
    def get_deleted_query(query, model_class):
        """Get only soft-deleted records"""
        if hasattr(model_class, 'is_deleted'):
            return query.filter(model_class.is_deleted == True)
        return query.filter(False)  # Return empty if no soft delete support
