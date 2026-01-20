import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [InputPool] %(message)s",
)


@dataclass
class Message:
    sender: str
    receiver: str
    msg_type: str
    payload: Any
    timestamp: float = field(default_factory=time.time)


# --- Strategy Enum ---
class Strategy(Enum):
    BLOCK = auto()
    DROP_NEW = auto()
    DROP_OLDEST = auto()
    DROP_LATEST = auto()


def _get_env_int(var_name: str, default: int) -> int:
    try:
        return int(os.getenv(var_name, default))
    except Exception:
        logging.warning(f"Invalid value for {var_name}, using default {default}")
        return default


def _get_env_strategy(var_name: str, default: Strategy) -> Strategy:
    val = os.getenv(var_name, default.name).upper()
    mapping = {
        "BLOCK": Strategy.BLOCK,
        "DROP_NEW": Strategy.DROP_NEW,
        "DROP_OLDEST": Strategy.DROP_OLDEST,
        "DROP_LATEST": Strategy.DROP_LATEST,
    }
    return mapping.get(val, default)


# --- Default configuration ---
POOL_SIZE = _get_env_int("MAX_SIZE", 5)
SENDER_LIMIT = _get_env_int("SENDER_LIMIT", POOL_SIZE)
TYPE_LIMIT = _get_env_int("TYPE_LIMIT", POOL_SIZE)
STRATEGY = _get_env_strategy("OVERFLOW_STRATEGY", Strategy.BLOCK)
