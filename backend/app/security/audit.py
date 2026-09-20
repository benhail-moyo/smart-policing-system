from datetime import datetime, timezone
from flask import request
from app import db
from app.models.models import AuditLog

def write_audit_event(user_id, event_type, event_metadata=None, **kwargs):
    """Write an audit event to the audit log."""
    # Support both old metadata parameter and new event_metadata for backwards compatibility
    metadata = event_metadata or kwargs.get('metadata', {})
    audit_log = AuditLog(
        user_id=user_id,
        event_type=event_type,
        event_metadata=metadata,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent", "")[:255],
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(audit_log)
    db.session.commit()
