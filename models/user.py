from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Any, Optional

from utils import parse_flexible_datetime


@dataclass(frozen=True)
class User:
    user_id: int
    username: str
    password_hash: str
    created_at: Optional[datetime]
    roles: List[str] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: Any, roles: Optional[List[str]] = None) -> Optional['User']:
        # From row
        """Create a User from a DB row (tuple/list or dict). Returns None if row is falsy."""
        if not row:
            return None

        if isinstance(row, dict):
            raw_id = row.get('user_id') or row.get('id') or row.get('uid')
            raw_name = row.get('username') or row.get('user') or row.get('name')
            raw_hash = row.get('password_hash') or row.get('password') or row.get('pwd')
            raw_date = row.get('created_at') or row.get('created')
        else:
            seq = list(row)
            raw_id = seq[0] if len(seq) > 0 else None
            raw_name = seq[1] if len(seq) > 1 else None
            raw_hash = seq[2] if len(seq) > 2 else None
            raw_date = seq[3] if len(seq) > 3 else None

        # Normalize created_at using shared parser
        created_at = parse_flexible_datetime(raw_date) if raw_date else None

        try:
            user_id = int(raw_id) if raw_id is not None else 0
        except (TypeError, ValueError):
            user_id = 0

        return cls(
            user_id=user_id,
            username=str(raw_name) if raw_name is not None else '',
            password_hash=str(raw_hash) if raw_hash is not None else '',
            created_at=created_at,
            roles=roles or [],
        )
