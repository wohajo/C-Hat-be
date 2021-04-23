import enum


class FriendsRequestStatus(enum.Enum):
    rejected = "rejected"
    pending = "pending"
    accepted = "accepted"
