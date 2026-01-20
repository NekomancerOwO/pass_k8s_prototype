import os
import time

from runtime.config import SUBJECT_NAME
from runtime.messaging import fetch_message, send_message
from runtime.state_engine import run

# --- Utility ---

order_counter = 0


def generate_order_id():
    global order_counter
    order_counter += 1
    return order_counter


# --- Subject Behavior ---


def wait_for_order():
    """
    The order intake waits for an ORDER message from a customer. The payload is a list of strings representing the ordered Items.
    Also includes simulation for a system crash.
    """

    msg = fetch_message(
        {
            "msg_type": ["ORDER"],
        }
    )
    if msg:
        if msg["msg_type"] == "ORDER":
            print(
                f"[{SUBJECT_NAME}] Received order from {msg['sender']}",
                flush=True,
            )
            return process_order(msg)
        if msg["msg_type"] == "CRASH":
            raise RuntimeError("Forced crash for testing restart policy")

    return wait_for_order  # Retry if request times out


def process_order(msg):
    """
    The order intake processes the order and adds a order number.
    """
    order_id = generate_order_id()
    items = msg["payload"]
    print(f"[{SUBJECT_NAME}] Processing Order No. {order_id}", flush=True)

    # Create new payload with order number
    processed_order = {
        "customer_name": msg["sender"],
        "order_id": order_id,
        "items": items,
    }

    time.sleep(1)
    return send_to_warehouse(processed_order)  # Transition to the next state


def send_to_warehouse(processed_order):
    """
    Implementation of a send state.
    """
    print(f"[{SUBJECT_NAME}] Sending message ...", flush=True)
    send_message(
        sender=SUBJECT_NAME,
        receiver="warehouse-manager",
        msg_type="WAREHOUSE_ORDER",
        payload=processed_order,
    )
    return wait_for_order  # Loop back to receive state


# --- Execution Start ---
if __name__ == "__main__":
    run(wait_for_order)
