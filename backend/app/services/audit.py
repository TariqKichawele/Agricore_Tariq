import json
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditLog, User


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return json.loads(json.dumps(value, default=str))


def write_audit(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    db.flush()
    entry = AuditLog(
        actor_id=actor.id if actor is not None else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=_json_safe(details) if details is not None else None,
    )
    db.add(entry)
    return entry
