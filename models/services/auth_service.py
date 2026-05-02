import re
from typing import Optional, List
from database import DatabaseManager
from models.user import User
from utils import validate_username, validate_password


class AuthService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return User object if valid, None otherwise."""
        clean_username = (username or "").strip()
        if not clean_username or len(clean_username) < 3 or len(clean_username) > 50:
            return None
        if re.search(r"\s", clean_username):
            return None
        if not password or not password.strip():
            return None

        user_row = self._db.authenticate_user(clean_username, password)
        if not user_row:
            return None

        roles = self._db.get_user_roles(user_row[0])
        return User.from_row(user_row, roles)

    def has_role(self, user: User, role_name: str) -> bool:
        """Check if user has specified role."""
        return role_name in user.roles

    def create_user_account(self, actor: User, username: str, password: str, account_type: str) -> int:
        """Create account as admin-only action.

        account_type supports: 'admin', 'employee' (mapped to 'staff'), 'staff'
        """
        if not actor or not self.has_role(actor, "admin"):
            raise PermissionError("Only admin can create new accounts.")

        is_valid, error = validate_username(username)
        if not is_valid:
            raise ValueError(error)
        clean_username = (username or "").strip()

        is_valid, error = validate_password(password)
        if not is_valid:
            raise ValueError(error)

        requested = (account_type or "").strip().lower()
        role_name = "staff" if requested == "employee" else requested
        if role_name not in ("admin", "staff"):
            raise ValueError("Account type must be Admin or Employee.")

        return self._db.create_user_with_role(clean_username, password, role_name)

    # Keep old name as alias for backward compatibility
    create_account = create_user_account

    def list_user_accounts(self, actor: User) -> List[dict]:
        if not actor or not self.has_role(actor, "admin"):
            raise PermissionError("Only admin can view accounts.")
        rows = self._db.fetch_users_with_roles()
        return [
            {
                "user_id": int(row[0]),
                "username": str(row[1]),
                "created_at": row[2],
                "is_active": bool(row[3]),
                "roles": str(row[4] or ""),
            }
            for row in rows
        ]

    # Keep old name as alias for backward compatibility
    list_accounts = list_user_accounts

    def set_account_active(self, actor: User, target_user_id: int, is_active: bool) -> None:
        if not actor or not self.has_role(actor, "admin"):
            raise PermissionError("Only admin can update account status.")
        if actor.user_id == target_user_id and not is_active:
            raise ValueError("You cannot disable your own account.")
        self._db.set_user_active(target_user_id, is_active)

    def reset_account_password(self, actor: User, target_user_id: int, new_password: str) -> None:
        if not actor or not self.has_role(actor, "admin"):
            raise PermissionError("Only admin can reset account passwords.")
        is_valid, error = validate_password(new_password)
        if not is_valid:
            raise ValueError(error)
        self._db.update_user_password(target_user_id, new_password)
