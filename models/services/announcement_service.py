from typing import List, Optional
from database import DatabaseManager
from models.user import User
from models.announcement import Announcement, AnnouncementSummary
from utils import is_admin


class AnnouncementService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def _require_admin(self, actor: User, action: str = "perform this action"):
        if not actor or not is_admin(actor):
            raise PermissionError(f"Only admin can {action}.")

    def create_announcement(self, actor: User, title: str, message: str,
                            recipient_type: str, specific_user_ids: Optional[List[int]] = None) -> int:
        """Create announcement as admin-only action."""
        self._require_admin(actor, "create announcements")
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
            recipient_ids = [user[0] for user in self._db.fetch_staff_users()]
        else:
            if not specific_user_ids:
                raise ValueError("Specific user IDs required when recipient type is 'specific'.")
            recipient_ids = specific_user_ids
        if not recipient_ids:
            raise ValueError("No recipients found.")
        return self._db.create_announcement(clean_title, clean_message, actor.user_id, recipient_ids)

    def get_announcements_for_user(self, user: User) -> List[Announcement]:
        if not user:
            return []
        return [Announcement.from_row(row) for row in self._db.fetch_announcements_for_user(user.user_id)]

    def get_all_announcements(self, actor: User) -> List[AnnouncementSummary]:
        self._require_admin(actor, "view all announcements")
        return [AnnouncementSummary.from_row(row) for row in self._db.fetch_all_announcements()]

    def mark_as_read(self, user: User, announcement_id: int) -> None:
        if not user or not isinstance(announcement_id, int) or announcement_id < 1:
            raise ValueError("Invalid parameters.")
        self._db.mark_announcement_as_read(announcement_id, user.user_id)

    def delete_announcement(self, actor: User, announcement_id: int) -> None:
        """Soft delete an announcement (admin only)."""
        self._require_admin(actor, "delete announcements")
        if not isinstance(announcement_id, int) or announcement_id < 1:
            raise ValueError("Invalid announcement ID.")
        self._db.soft_delete_announcement(announcement_id)

    def restore_announcement(self, actor: User, announcement_id: int) -> None:
        """Restore a soft-deleted announcement (admin only)."""
        self._require_admin(actor, "restore announcements")
        if not isinstance(announcement_id, int) or announcement_id < 1:
            raise ValueError("Invalid announcement ID.")
        self._db.restore_announcement(announcement_id)

    def permanently_delete_announcement(self, actor: User, announcement_id: int) -> None:
        """Permanently delete an announcement (admin only)."""
        self._require_admin(actor, "permanently delete announcements")
        if not isinstance(announcement_id, int) or announcement_id < 1:
            raise ValueError("Invalid announcement ID.")
        self._db.permanently_delete_announcement(announcement_id)

    def get_deleted_announcements(self, actor: User) -> List[AnnouncementSummary]:
        """Get all soft-deleted announcements (admin only)."""
        self._require_admin(actor, "view deleted announcements")
        return [AnnouncementSummary.from_row(row) for row in self._db.fetch_deleted_announcements()]

    def get_staff_list(self, actor: User) -> List[dict]:
        self._require_admin(actor, "view staff list")
        return [{"user_id": int(row[0]), "username": str(row[1])} for row in self._db.fetch_staff_users()]
