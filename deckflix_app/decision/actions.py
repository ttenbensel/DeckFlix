from enum import Enum


class Action(str, Enum):
    NEW = "NEW"
    UPGRADE = "UPGRADE"
    DUPLICATE = "DUPLICATE"
    DOWNGRADE = "DOWNGRADE"
    BELOW_TARGET = "BELOW_TARGET"
    REVIEW = "REVIEW"
