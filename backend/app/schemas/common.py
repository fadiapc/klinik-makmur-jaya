"""
common.py — Shared Pydantic schemas used across multiple modules.

Provides:
  • PaginationParams  — query parameters for paginated list endpoints
  • PaginatedResponse — generic typed wrapper for list API responses
  • MessageResponse   — simple success/info text response (re-export friendly)
  • SortOrder         — asc/desc enum
"""

from __future__ import annotations

import enum
from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

# Generic type variable for the item type inside paginated responses
T = TypeVar("T")


# ── Sort order ────────────────────────────────────────────────────────────────


class SortOrder(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


# ── Pagination query parameters ───────────────────────────────────────────────


class PaginationParams(BaseModel):
    """
    Standard pagination + sorting query parameters.

    Usage in a route:
        @router.get("/items")
        async def list_items(params: PaginationParams = Depends()):
            ...
    """

    page: int = Field(default=1, ge=1, description="Page number, 1-indexed")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page (max 100)",
    )

    @property
    def offset(self) -> int:
        """SQL OFFSET value derived from page and page_size."""
        return (self.page - 1) * self.page_size


# ── Generic paginated response ─────────────────────────────────────────────────


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated list response envelope.

    Example JSON:
        {
          "items": [...],
          "total": 123,
          "page": 1,
          "page_size": 20,
          "total_pages": 7,
          "has_next": true,
          "has_prev": false
        }
    """

    items: List[T]
    total: int = Field(description="Total number of items matching the filter")
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def build(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Factory: calculate total_pages and has_next/has_prev automatically."""
        import math

        total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


# ── Simple message response ────────────────────────────────────────────────────


class MessageResponse(BaseModel):
    """Generic text response for success/info endpoints."""

    message: str
