from typing import Optional
from database import DatabaseManager
from models.user import User

class AuthService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return User object if valid, None otherwise."""
        # Validate input
        if not username or not username.strip():
            return None
        if not password:
            return None

        # Let DatabaseError bubble up so UI can show a real message instead
        # of silently presenting it as invalid credentials.
        user_row = self._db.authenticate_user(username.strip(), password)
        if not user_row:
            return None

        # Get user roles using user_id from the row
        user_id = user_row[0]
        roles = self._db.get_user_roles(user_id)

        return User.from_row(user_row, roles)

    def has_role(self, user: User, role_name: str) -> bool:
        """Check if user has specified role."""
        return role_name in user.roles

    def create_account(self, actor: User, username: str, password: str, account_type: str) -> int:
        """Create account as admin-only action.

        account_type supports: 'admin', 'employee' (mapped to 'staff'), 'staff'
        """
        if not actor or not self.has_role(actor, "admin"):
            raise PermissionError("Only admin can create new accounts.")

        clean_username = (username or "").strip()
        if len(clean_username) < 3:
            raise ValueError("Username must be at least 3 characters.")
        if len(password or "") < 6:
            raise ValueError("Password must be at least 6 characters.")

        requested = (account_type or "").strip().lower()
        role_name = "staff" if requested == "employee" else requested
        if role_name not in ("admin", "staff"):
            raise ValueError("Account type must be Admin or Employee.")

        return self._db.create_user_with_role(clean_username, password, role_name)

    def list_accounts(self, actor: User) -> list[dict]:
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

    def set_account_active(self, actor: User, target_user_id: int, is_active: bool) -> None:
        if not actor or not self.has_role(actor, "admin"):
            raise PermissionError("Only admin can update account status.")
        if actor.user_id == target_user_id and not is_active:
            raise ValueError("You cannot disable your own account.")
        self._db.set_user_active(target_user_id, is_active)

    def reset_account_password(self, actor: User, target_user_id: int, new_password: str) -> None:
        if not actor or not self.has_role(actor, "admin"):
            raise PermissionError("Only admin can reset account passwords.")
        if len(new_password or "") < 6:
            raise ValueError("Password must be at least 6 characters.")
        self._db.update_user_password(target_user_id, new_password)
