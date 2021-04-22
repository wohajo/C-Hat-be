import enum


class InvitationStatus(enum.Enum):
    rejected = "rejected"
    pending = "pending"
    accepted = "accepted"
