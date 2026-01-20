import os
import time

from runtime.config import SUBJECT_NAME
from runtime.messaging import (
    fetch_message,
    headless_send_message,
    headless_send_message_all,
    headless_send_message_n,
    send_message,
)
from runtime.state_engine import run

# --- Subject Behavior ---


def example_receive_state():
    """
    Implementation of a branching receive state. Continues asking for responses from the input pool until a specific message is present. Transitions into different states depending on the message received.
    """

    msg = fetch_message(
        {
            "sender": "external-subject",
            "msg_type": ["START", "END"],
        }
    )
    if msg:
        if msg["msg_type"] == "START":
            print(
                f"[{SUBJECT_NAME}] Received START message from {msg['sender']}",
                flush=True,
            )
            return example_function_state(msg)
        if msg["msg_type"] == "END":
            print(
                f"[{SUBJECT_NAME}] Received END message from {msg['sender']}",
                flush=True,
            )
            return example_end_state()

    return example_receive_state  # Retry if request times out


def example_function_state(msg):
    """
    Implementation of a function state.
    """
    print(f"[{SUBJECT_NAME}] Doing work...", flush=True)
    time.sleep(5)
    return example_send_state(msg)  # Transition to the next state


def example_send_state(msg):
    """
    Implementation of a send state.
    """
    print(f"[{SUBJECT_NAME}] Sending message ...", flush=True)
    send_message(
        sender=SUBJECT_NAME,
        receiver="multi-example-subject",
        msg_type="example_message",
        payload=msg["payload"],
    )
    return example_receive_state  # Loop back to receive state


def example_headless_send_state(msg):
    """
    Implementation of a send state.
    """
    print(f"[{SUBJECT_NAME}] Sending message ...", flush=True)
    headless_send_message_all(
        sender=SUBJECT_NAME,
        receiver="multi-example-subject-headless",
        msg_type="headless_example_message",
        payload=msg["payload"],
    )
    return example_receive_state  # Loop back to receive state


def example_end_state():
    """
    Implementation of an end state. Kubernetes will keep resurrecting containers if they finish executing. The restart policy can be modified to change this,
    however doing so would affect the desired self healing and resilience mechanism. In this example the container is just put to sleep indefinitely.
    """
    print(f"[{SUBJECT_NAME}] Reached END state. Stopping subject behavior.", flush=True)
    while True:
        time.sleep(3600)


# --- Execution Start ---
if __name__ == "__main__":
    run(example_receive_state)
