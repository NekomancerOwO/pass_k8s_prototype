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

item_count = 200


def send_inventory_promise():
    """
    Inventory System sends promise that item quantity is above 100
    """
    promise = create_promise_payload(PromiseType.STATE.value, 100)

    print(f"[{SUBJECT_NAME}] Sending promise ...", flush=True)
    send_message(
        sender=SUBJECT_NAME,
        receiver="inventory-monitor",
        msg_type="PROMISE",
        payload=promise,
    )
    return receive_request


def receive_request():
    msg = fetch_message(
        {
            "msg_type": ["REQUEST", "UPDATE"],
        }
    )
    if msg:
        if msg["msg_type"] == "REQUEST":
            return send_response()
        if msg["msg_type"] == "UPDATE":
            return update_inventory(msg)

    return receive_request


def update_inventory(msg):
    """
    Implementation of a function state.
    """
    global item_count
    item_count = msg["payload"]
    print(
        f"[{SUBJECT_NAME}] Updating Inventory. New Item Count = {item_count}",
        flush=True,
    )
    return receive_request()


def send_response():
    """
    Service Desk sends promise to respond within 24 hours.
    """
    print(f"[{SUBJECT_NAME}] Sending Item Count ...", flush=True)
    send_message(
        sender=SUBJECT_NAME,
        receiver="inventory-monitor",
        msg_type="RESPONSE",
        payload=item_count,
    )
    return receive_request


# --- Execution Start ---
if __name__ == "__main__":
    run(send_inventory_promise)
