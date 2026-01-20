import os
import random
import time

from runtime.config import SUBJECT_NAME
from runtime.messaging import (
    fetch_message,
    send_message,
)
from runtime.state_engine import run

# --- Warehouse items ---
WAREHOUSE_MAP = {
    "A1": ["Red Mug", "Blue Mug", "Green Mug"],
    "A2": ["Espresso Machine", "Coffee Grinder"],
    "B1": ["Wireless Mouse", "Keyboard", "USB Hub"],
    "B2": ["Notebook", "Pen Set", "Stapler"],
    "C1": ["LED Lamp", "Desk Organizer"],
    "C2": ["Cookbook", "Frying Pan", "Cutting Board"],
    "D1": ["Water Bottle", "Travel Mug", "Lunch Box"],
    "D2": ["Headphones", "Charger", "Phone Case"],
}


# --- Subject Behavior ---


def example_receive_state():
    """
    Receives signals from external subjects.
    """
    msg = fetch_message(
        {
            "sender": "external-subject",
            "msg_type": ["START"],
        }
    )
    if msg:
        if msg["msg_type"] == "START":
            print(
                f"[{SUBJECT_NAME}] Received TEST signal: sending batch orders...",
                flush=True,
            )
            return send_batch_orders_state()

    return example_receive_state  # Retry if request times out


def send_batch_orders_state():
    """
    Simulates 10 customer orders with 2-6 items each.
    """
    num_orders = 10
    for order_num in range(1, num_orders + 1):
        all_items = [item for sublist in WAREHOUSE_MAP.values() for item in sublist]
        order_items = random.sample(all_items, random.randint(2, 6))

        order_payload = {
            "sender": SUBJECT_NAME,
            "receiver": "order-intake",
            "msg_type": "ORDER",
            "payload": order_items,
        }

        print(f"[{SUBJECT_NAME}] Sending order {order_num}: {order_items}", flush=True)
        send_message(**order_payload)
        time.sleep(1)  # slight delay between orders

    print(f"[{SUBJECT_NAME}] Finished sending batch orders.", flush=True)
    return example_receive_state  # Back to receive state


# --- Execution Start ---
if __name__ == "__main__":
    run(example_receive_state)
