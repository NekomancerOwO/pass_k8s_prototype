import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class PromiseType(Enum):
    TIMEOUT = "timeout"  # Promise promising an outcome before a certain timestamp. Assessment only returns False or unknown
    STATE = "state"  # Promise comparing a monitored value to a promised value


class PromiseState(Enum):
    UNKNOWN = "unknown"
    KEPT = "kept"
    BROKEN = "broken"


@dataclass
class Promise:
    condition: Callable[
        ..., Optional[bool]
    ]  # Stores assessment function inside promise object, Receiving Subject declares assessment logic when receiving promise
    created_at: float = field(default_factory=time.time)
    state: PromiseState = PromiseState.UNKNOWN

    def assess(self, *args, **kwargs) -> PromiseState:  # Allow for optional parameters
        result = self.condition(*args, **kwargs)

        if result is True:
            self.state = PromiseState.KEPT
        elif result is False:
            self.state = PromiseState.BROKEN
        else:
            self.state = PromiseState.UNKNOWN

        return self.state


def create_promise_payload(type, condition):
    return {
        "promise": {
            "type": type,
            "condition": condition,
        }
    }
