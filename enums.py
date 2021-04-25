import enum


class FriendsRequestStatus(enum.Enum):
    REJECTED = "rejected"
    PENDING = "pending"
    ACCEPTED = "accepted"
