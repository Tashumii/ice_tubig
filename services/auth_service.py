from typing import Optional, List
from database import DatabaseManager, DatabaseError
from models.user import User

class AuthService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return User object if valid, None otherwise."""
        try:
            # Validate input
            if not username or not username.strip():
                return None
            if not password:
                return None
            
            user_row = self._db.authenticate_user(username.strip(), password)
            if not user_row:
                return None
            
            # Get user roles using user_id from the row
            user_id = user_row[0]
            roles = self._db.get_user_roles(user_id)
            
            return User.from_row(user_row, roles)
        except DatabaseError:
            return None

    def has_role(self, user: User, role_name: str) -> bool:
        """Check if user has specified role."""
        return role_name in user.roles
