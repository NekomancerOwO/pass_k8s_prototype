import os
import time
from collections import defaultdict

from runtime.config import SUBJECT_NAME
from runtime.lifecycle import termination_requested
from runtime.messaging import fetch_message, send_message
from runtime.state_engine import run

# --- Orders ---

order_customer = {}  # order_id, customer_name
order_item_count = {}  # order_id, number of items
order_items = defaultdict(list)  # order_id, list of items[]


# --- Subject Behavior ---


def shipping_receive_state():
    """
    The shipping manager waits for order jobs or item deliveries
    """
    if termination_requested():
        print(f"[{SUBJECT_NAME}] PASS end state reached, terminating", flush=True)
        return None

    msg = fetch_message(
        {
            "msg_type": ["SHIPPING_ORDER", "ITEM"],
        }
    )
    if msg:
        if msg["msg_type"] == "SHIPPING_ORDER":
            return register_order(msg)
        elif msg["msg_type"] == "ITEM":
            return collect_item(msg)

    # Retry if no message
    return shipping_receive_state


def register_order(msg):
    """
    Records a new order internally.
    """
    order_id = msg["payload"]["order_id"]
    customer_name = msg["payload"]["customer_name"]
    expected_items = msg["payload"]["expected_items"]

    order_customer[order_id] = customer_name
    order_item_count[order_id] = expected_items
    order_items[order_id] = []

    print(
        f"[{SUBJECT_NAME}] Recorded order {order_id} from customer {customer_name}; expecting {expected_items} items.",
        flush=True,
    )

    return shipping_receive_state


def collect_item(msg):
    """
    Adds an item to an existing order and checks if order is complete.
    """
    order_id = msg["payload"]["order_id"]
    item = msg["payload"]["item"]

    if order_id not in order_item_count:
        print(
            f"[{SUBJECT_NAME}] WARNING: Received ITEM for unknown order {order_id}",
            flush=True,
        )
        return shipping_receive_state

    order_items[order_id].append(item)
    print(
        f"[{SUBJECT_NAME}] Added item to order {order_id}: {item} "
        f"({len(order_items[order_id])}/{order_item_count[order_id]})",
        flush=True,
    )

    if len(order_items[order_id]) >= order_item_count[order_id]:
        return complete_order(order_id)

    return shipping_receive_state


def complete_order(order_id):
    """
    The finished order gets sent to the customer
    """
    customer = order_customer[order_id]
    items = order_items[order_id]
    print(
        f"[{SUBJECT_NAME}] Sending completed order {order_id} to customer {customer}. Order items: {items}",
        flush=True,
    )

    # Deleting order from internal system
    del order_customer[order_id]
    del order_item_count[order_id]
    del order_items[order_id]

    return shipping_receive_state


# --- Execution Start ---
if __name__ == "__main__":
    run(shipping_receive_state)
