from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple, Any, Optional

@dataclass(frozen=True)
class User:
    user_id: int
    username: str
    password_hash: str
    created_at: Optional[datetime]
    roles: List[str] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: Any, roles: Optional[List[str]] = None) -> Optional['User']:
        """Create a User from a DB row.

        Accepts sequence-like rows (tuple/list) or dict-like rows.
        Returns None if `row` is falsy.
        """
        if not row:
            return None

        # Dict-like access
        if isinstance(row, dict):
            user_id = row.get('user_id') or row.get('id') or row.get('uid')
            username = row.get('username') or row.get('user') or row.get('name')
            password_hash = row.get('password_hash') or row.get('password') or row.get('pwd')
            created_at = row.get('created_at') or row.get('created') or None
        else:
            seq = list(row)
            user_id = seq[0] if len(seq) > 0 else None
            username = seq[1] if len(seq) > 1 else None
            password_hash = seq[2] if len(seq) > 2 else None
            created_at = seq[3] if len(seq) > 3 else None

        # Normalize created_at into datetime if possible
        if isinstance(created_at, str):
            try:
                created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            except Exception:
                try:
                    created_at = datetime.fromisoformat(created_at)
                except Exception:
                    created_at = None
        elif not isinstance(created_at, datetime):
            created_at = None

        try:
            user_id = int(user_id) if user_id is not None else 0
        except Exception:
            user_id = 0

        username = str(username) if username is not None else ''
        password_hash = str(password_hash) if password_hash is not None else ''

        return cls(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            created_at=created_at,
            roles=roles or [],
        )
