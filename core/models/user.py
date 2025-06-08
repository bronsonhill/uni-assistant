from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class User:
    email: str
    name: Optional[str] = None
    subscription_status: bool = False
    subscription_end: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    last_login: Optional[datetime] = None
    login_count: int = 0
    preferences: Dict[str, Any] = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert user object to dictionary format for storage"""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        for field in ['subscription_end', 'created_at', 'last_updated', 'last_login']:
            if data[field]:
                data[field] = data[field].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user object from dictionary data"""
        # Convert ISO format strings back to datetime objects
        for field in ['subscription_end', 'created_at', 'last_updated', 'last_login']:
            if field in data and data[field]:
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)

    def update(self, **kwargs) -> None:
        """Update user fields"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.last_updated = datetime.now()

    def is_subscription_active(self) -> bool:
        """Check if user's subscription is active"""
        if not self.subscription_status:
            return False
        if not self.subscription_end:
            return False
        return datetime.now() < self.subscription_end 