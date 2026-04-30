from typing import List, Optional
from database import DatabaseManager
from models.user import User
from models.announcement import Announcement, AnnouncementSummary

class AnnouncementService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def create_announcement(self, actor: User, title: str, message: str, recipient_type: str, specific_user_ids: Optional[List[int]] = None) -> int:
        """Create announcement as admin-only action.
        
        Args:
            actor: User creating the announcement (must be admin)
            title: Announcement title
            message: Announcement message
            recipient_type: 'all' for all staff, 'specific' for specific users
            specific_user_ids: List of user IDs when recipient_type is 'specific'
        
        Returns:
            announcement_id
        """
        if not actor or 'admin' not in actor.roles:
            raise PermissionError("Only admin can create announcements.")
        
        clean_title = (title or "").strip()
        if not clean_title:
            raise ValueError("Title is required.")
        if len(clean_title) > 200:
            raise ValueError("Title must be 200 characters or fewer.")
        
        clean_message = (message or "").strip()
        if not clean_message:
            raise ValueError("Message is required.")
        
        recipient_type = (recipient_type or "").strip().lower()
        if recipient_type not in ('all', 'specific'):
            raise ValueError("Recipient type must be 'all' or 'specific'.")
        
        if recipient_type == 'all':
            staff_users = self._db.fetch_staff_users()
            recipient_ids = [user[0] for user in staff_users]
        else:
            if not specific_user_ids:
                raise ValueError("Specific user IDs required when recipient type is 'specific'.")
            recipient_ids = specific_user_ids
        
        if not recipient_ids:
            raise ValueError("No recipients found.")
        
        return self._db.create_announcement(clean_title, clean_message, actor.user_id, recipient_ids)

    def get_announcements_for_user(self, user: User) -> List[Announcement]:
        """Get all announcements for a user."""
        if not user:
            return []
        rows = self._db.fetch_announcements_for_user(user.user_id)
        return [Announcement.from_row(row) for row in rows]

    def get_all_announcements(self, actor: User) -> List[AnnouncementSummary]:
        """Get all announcements (admin only)."""
        if not actor or 'admin' not in actor.roles:
            raise PermissionError("Only admin can view all announcements.")
        rows = self._db.fetch_all_announcements()
        return [AnnouncementSummary.from_row(row) for row in rows]

    def mark_as_read(self, user: User, announcement_id: int) -> None:
        """Mark announcement as read."""
        if not user or not isinstance(announcement_id, int) or announcement_id < 1:
            raise ValueError("Invalid parameters.")
        self._db.mark_announcement_as_read(announcement_id, user.user_id)

    def delete_announcement(self, actor: User, announcement_id: int) -> None:
        """Delete announcement (admin only)."""
        if not actor or 'admin' not in actor.roles:
            raise PermissionError("Only admin can delete announcements.")
        if not isinstance(announcement_id, int) or announcement_id < 1:
            raise ValueError("Invalid announcement ID.")
        self._db.delete_announcement(announcement_id)

    def get_staff_list(self, actor: User) -> List[dict]:
        """Get list of staff users for selection (admin only)."""
        if not actor or 'admin' not in actor.roles:
            raise PermissionError("Only admin can view staff list.")
        rows = self._db.fetch_staff_users()
        return [{"user_id": int(row[0]), "username": str(row[1])} for row in rows]
