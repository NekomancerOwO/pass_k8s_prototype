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
from runtime.promise import Promise, PromiseState, PromiseType
from runtime.state_engine import run

# --- Subject Behavior ---


def send_service_request():
    """
    Implementation of a send state.
    """
    print(f"[{SUBJECT_NAME}] Sending service request ...", flush=True)
    send_message(
        sender=SUBJECT_NAME,
        receiver="service-desk",
        msg_type="REQUEST",
        payload="service_request",
    )
    return receive_promise


def receive_promise():
    """
    Customer subject receives timeout promise from service desk
    """
    msg = fetch_message(
        {
            "sender": "service-desk",
            "msg_type": ["PROMISE"],
        }
    )
    if msg:
        promise_payload = msg["payload"]["promise"]
        promise_type = PromiseType(promise_payload["type"])
        if promise_type != PromiseType.TIMEOUT:
            raise RuntimeError("Invalid Promise Received!")

        # Create promise assessment logic. In this implementation the Promise is considered kept if the message arrives and the assessment does not return False.
        def promise_condition():
            if time.time() > promise_payload["condition"]:
                return False  # Promise Broken
            return None  # Promise Unknown

        timeout_promise = Promise(condition=promise_condition)
        return receive_response(timeout_promise)

    return receive_promise  # Retry if request times out


def receive_response(timeout_promise):
    """
    Customer subject receives timeout promise from service desk
    """
    msg = fetch_message(
        {
            "sender": "service-desk",
            "msg_type": ["RESPONSE"],
        }
    )
    if msg:
        print(f"[{SUBJECT_NAME}] Response Received ...", flush=True)
        return end_state

    promise_state = timeout_promise.assess()

    if promise_state == PromiseState.BROKEN:
        print(
            f"[{SUBJECT_NAME}] Promise Broken. Returning to send state ...", flush=True
        )
        return send_service_request  # Loop back to beginning if promise times out
    if promise_state == PromiseState.UNKNOWN:
        return receive_response  # Keep waiting for response if promise is not broken


def end_state():
    """
    Implementation of an end state. Kubernetes will keep resurrecting containers if they finish executing. The restart policy can be modified to change this,
    however doing so would affect the desired self healing and resilience mechanism. In this example the container is just put to sleep indefinitely.
    """
    if termination_requested():
        print(f"[{SUBJECT_NAME}] PASS end state reached, terminating", flush=True)
        return None
    print(f"[{SUBJECT_NAME}] Reached END state. Stopping subject behavior.", flush=True)
    while True:
        time.sleep(3600)


# --- Execution Start ---
if __name__ == "__main__":
    run(send_service_request)
