from enum import Enum


class UserRole(str, Enum):
    LEARNER = "LEARNER"
    INSTRUCTOR = "INSTRUCTOR"


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class SessionType(str, Enum):
    LEARNING = "LEARNING"
    EXAM = "EXAM"


class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ENDED = "ENDED"


class EventType(str, Enum):
    EYES_CLOSED_LONG = "EYES_CLOSED_LONG"
    YAWN_DETECTED = "YAWN_DETECTED"
    HEAD_NOD_DETECTED = "HEAD_NOD_DETECTED"
    LOOK_AWAY_DETECTED = "LOOK_AWAY_DETECTED"
    FACE_NOT_DETECTED = "FACE_NOT_DETECTED"
    MULTIPLE_FACES_DETECTED = "MULTIPLE_FACES_DETECTED"
    PHONE_DETECTED = "PHONE_DETECTED"
    TAB_HIDDEN = "TAB_HIDDEN"
    CAMERA_LOST = "CAMERA_LOST"
    CONNECTION_LOST = "CONNECTION_LOST"


class EventSource(str, Enum):
    AI_LEARNING = "AI_LEARNING"
    AI_EXAM = "AI_EXAM"
    BROWSER = "BROWSER"
    SYSTEM = "SYSTEM"


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
