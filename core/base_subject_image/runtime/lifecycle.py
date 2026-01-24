import signal
import threading

from runtime.config import SUBJECT_NAME

terminate_requested = threading.Event()


def _handle_sigterm(signum, frame):
    print(f"[{SUBJECT_NAME}] SIGTERM received", flush=True)
    terminate_requested.set()


signal.signal(signal.SIGTERM, _handle_sigterm)


def termination_requested():
    return terminate_requested.is_set()
