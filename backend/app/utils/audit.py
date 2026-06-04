"""
audit.py — Async helper for writing immutable audit log entries.

Usage:
    from app.utils.audit import log_audit

    await log_audit(
        db=db,
        user_id=current_user.id,
        action="LOGIN",
        module="AUTH",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )

Design notes:
• Uses `db.flush()` (not `commit()`) — the session is committed by the
  get_db() dependency at the end of the request.  This keeps the audit row
  in the same transaction as the business operation so they succeed or fail
  together (ACID compliance).
• All fields are optional at the call site (except db/action/module) so
  callers only supply what they know.
• Never raises — logging failures must not break the request flow.
  Errors are captured and logged to the Python logger instead.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AuditLog

logger = logging.getLogger(__name__)


async def log_audit(
    db: AsyncSession,
    action: str,
    module: str,
    user_id: Optional[int] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    old_value: Optional[dict[str, Any]] = None,
    new_value: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """
    Insert an audit log row into the current DB session.

    Args:
        db:          Active async session — the row is flushed but NOT committed.
        action:      SCREAMING_SNAKE_CASE action name (e.g. LOGIN, CREATE_PRODUCT).
        module:      Application module name (e.g. AUTH, PRODUCT, ORDER).
        user_id:     Internal PK of the acting user.  None for anonymous actions.
        target_type: ORM entity name of the changed record (e.g. "User", "Product").
        target_id:   PK of the affected entity row.  None for non-entity actions.
        old_value:   Before-state dict (serialised entity, redacted sensitive fields).
        new_value:   After-state dict.
        ip_address:  Client IP (IPv4 or IPv6).
        user_agent:  HTTP User-Agent header value.
    """
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            module=module,
            target_type=target_type,
            target_id=target_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(entry)
        await db.flush()  # assigns entry.id without committing the transaction
        logger.debug(
            "Audit log written | action=%s module=%s user_id=%s target=%s[%s]",
            action,
            module,
            user_id,
            target_type,
            target_id,
        )
    except Exception as exc:  # pragma: no cover
        # Audit failure must not propagate — log and continue
        logger.error(
            "Failed to write audit log | action=%s error=%s",
            action,
            exc,
            exc_info=True,
        )
