import os
import time

from runtime.config import SUBJECT_NAME
from runtime.lifecycle import termination_requested
from runtime.messaging import (
    fetch_message,
    headless_send_message,
    headless_send_message_all,
    headless_send_message_n,
    send_message,
)
from runtime.promise import PromiseType, create_promise_payload
from runtime.state_engine import run

# --- Subject Behavior ---


def receive_service_request():
    """
    Implementation of a branching receive state. Continues asking for responses from the input pool until a specific message is present. Transitions into different states depending on the message received.
    """

    if termination_requested():
        print(f"[{SUBJECT_NAME}] PASS end state reached, terminating", flush=True)
        return None

    msg = fetch_message(
        {
            "msg_type": ["REQUEST", "RESPOND"],
        }
    )
    if msg:
        if msg["msg_type"] == "REQUEST":
            return send_promise()
        if msg["msg_type"] == "RESPOND":
            return send_response()

    return receive_service_request  # Retry if request times out


def send_promise():
    """
    Service Desk sends promise to respond within 24 hours.
    """
    promise = create_promise_payload(PromiseType.TIMEOUT.value, time.time() + 5)

    print(f"[{SUBJECT_NAME}] Sending promise ...", flush=True)
    send_message(
        sender=SUBJECT_NAME,
        receiver="customer",
        msg_type="PROMISE",
        payload=promise,
    )
    return receive_service_request  # Loop back to receive state


def example_function_state():
    """
    Implementation of a function state.
    """
    print(f"[{SUBJECT_NAME}] Doing work...", flush=True)
    time.sleep(10)
    return send_response  # Transition to the next state


def send_response():
    """
    Service Desk sends promise to respond within 24 hours.
    """
    print(f"[{SUBJECT_NAME}] Sending response ...", flush=True)
    send_message(
        sender=SUBJECT_NAME,
        receiver="customer",
        msg_type="RESPONSE",
        payload="service_response",
    )
    return example_end_state


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
    run(receive_service_request)
