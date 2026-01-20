import logging
import threading
import time
from collections import defaultdict, deque
from typing import Dict, Mapping, Optional

from input_pool.config import Message, Strategy


class InputPool:
    def __init__(
        self,
        max_size: int,
        per_sender_limit: Optional[int] = None,
        per_type_limit: Optional[int] = None,
        strategy: Strategy = Strategy.BLOCK,
    ):
        self.condition = threading.Condition()
        self.pool: deque[Message] = deque()
        self.sender_counts = defaultdict(int)
        self.type_counts = defaultdict(int)

        self.max_size = max_size
        self.per_sender_limit = per_sender_limit
        self.per_type_limit = per_type_limit
        self.strategy = strategy

    def _fits_constraints(self, message: Message) -> bool:
        if len(self.pool) >= self.max_size:
            return False

        if (
            self.per_sender_limit
            and self.sender_counts[message.sender] >= self.per_sender_limit
        ):
            return False

        if (
            self.per_type_limit
            and self.type_counts[message.msg_type] >= self.per_type_limit
        ):
            return False

        return True

    def select_message(self, msg: Message, criteria: Mapping[str, object]) -> bool:
        if not criteria:
            return False
        for key, expected in criteria.items():
            actual = getattr(msg, key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True

    def add_message(self, message: Message) -> bool:
        with self.condition:
            if self._fits_constraints(message):
                self.pool.append(message)
                self.sender_counts[message.sender] += 1
                self.type_counts[message.msg_type] += 1
                self.condition.notify_all()
                logging.info(f"[ACCEPTED] message: {message}")
                return True

            # Handle overflow strategies
            removed_message: Optional[Message] = None
            strategy_name = self.strategy.name  # Enum name as string

            if self.strategy == Strategy.BLOCK:
                logging.info(f"[{strategy_name}] message: {message}")
                return False

            if self.strategy == Strategy.DROP_NEW:
                logging.info(f"[{strategy_name}] message: {message}")
                return True

            if self.strategy == Strategy.DROP_OLDEST and self.pool:
                removed_message = self.pool.popleft()
            elif self.strategy == Strategy.DROP_LATEST and self.pool:
                removed_message = self.pool.pop()

            if removed_message:
                self.sender_counts[removed_message.sender] -= 1
                self.type_counts[removed_message.msg_type] -= 1
                logging.info(
                    f"[{strategy_name}] removed message: {removed_message} -> added message: {message}"
                )
            else:
                logging.info(f"[{strategy_name}] added message: {message}")

            self.pool.append(message)
            self.sender_counts[message.sender] += 1
            self.type_counts[message.msg_type] += 1
            self.condition.notify_all()
            return True

    def receive_blocking(
        self, criteria: Dict, timeout: float = 30.0
    ) -> Optional[Message]:
        with self.condition:
            start_time = time.time()

            while True:
                for i, msg in enumerate(self.pool):
                    if self.select_message(msg, criteria):
                        del self.pool[i]
                        self.sender_counts[msg.sender] -= 1
                        self.type_counts[msg.msg_type] -= 1
                        return msg

                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return None

                self.condition.wait(timeout - elapsed)
