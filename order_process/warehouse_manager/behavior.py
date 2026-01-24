import os
import time

from runtime.config import SUBJECT_NAME
from runtime.lifecycle import termination_requested
from runtime.messaging import fetch_message, headless_send_message, send_message
from runtime.state_engine import run

# --- Subject Behavior ---


def wait_for_warehouse_order():
    """
    The order intake waits for an ORDER message from a customer. The payload is a list of strings representing the ordered Items.
    Also includes simulation for a system crash.
    """

    if termination_requested():
        print(f"[{SUBJECT_NAME}] PASS end state reached, terminating", flush=True)
        return None

    msg = fetch_message(
        {
            "sender": ["order-intake"],
            "msg_type": ["WAREHOUSE_ORDER"],
        }
    )
    if msg:
        print(
            f"[{SUBJECT_NAME}] Received warehouse order from {msg['sender']}",
            flush=True,
        )
        return register_order_with_shipping_manager(msg)

    return wait_for_warehouse_order  # Retry if request times out


def register_order_with_shipping_manager(msg):
    """
    This sends the item amount of an order to the shipping manager, so they know how many items they can expect from the warehouse workers.
    """
    order = msg["payload"]
    customer_name = order["customer_name"]
    order_id = order["order_id"]
    items = order["items"]

    print(
        f"[{SUBJECT_NAME}] Registering order No. {order_id} with shipping manager",
        flush=True,
    )

    send_message(
        sender=SUBJECT_NAME,
        receiver="shipping-manager",
        msg_type="SHIPPING_ORDER",
        payload={
            "customer_name": customer_name,
            "order_id": order_id,
            "expected_items": len(items),
        },
    )

    return send_items_to_warehouse_workers(order)


def send_items_to_warehouse_workers(order):
    """
    This splits the order into individual items and sends each item to a warehouse worker.
    """
    order_id = order["order_id"]
    items = order["items"]

    for item in items:
        print(
            f"[{SUBJECT_NAME}] Sending item '{item}' for order {order_id} to warehouse worker",
            flush=True,
        )
        send_message(
            sender=SUBJECT_NAME,
            receiver="warehouse-worker",
            msg_type="JOB",
            payload={
                "order_id": order_id,
                "item": item,
            },
        )

    return wait_for_warehouse_order  # Return to receive state


# --- Execution Start ---
if __name__ == "__main__":
    run(wait_for_warehouse_order)
