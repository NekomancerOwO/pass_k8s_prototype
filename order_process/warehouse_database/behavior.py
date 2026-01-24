import os
import time

from runtime.config import SUBJECT_NAME
from runtime.lifecycle import termination_requested
from runtime.messaging import fetch_message, send_message
from runtime.state_engine import run

# --- Warehouse Database ---

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


def receive_item_query():
    """
    Database waits for an ITEM_QUERY from a warehouse worker.
    """
    if termination_requested():
        print(f"[{SUBJECT_NAME}] PASS end state reached, terminating", flush=True)
        return None

    msg = fetch_message(
        {
            "msg_type": ["ITEM_QUERY"],
        }
    )

    if msg:
        item = msg["payload"]["item"]
        print(
            f"[{SUBJECT_NAME}] Received query for '{item}' from {msg['sender']}",
            flush=True,
        )
        return lookup_item_location(msg)

    return receive_item_query  # Retry if no message yet


def lookup_item_location(msg):
    """
    Search the internal database for the item location
    """
    item = msg["payload"]["item"]
    location = "UNKNOWN"

    for shelf, items_on_shelf in WAREHOUSE_MAP.items():
        if item in items_on_shelf:
            location = shelf
            break

    print(f"[{SUBJECT_NAME}] Item '{item}' is located at '{location}'", flush=True)
    msg["payload"]["location"] = location
    return send_item_location(msg)


def send_item_location(msg):
    """
    Send state: send item location back to the warehouse worker.
    """
    item = msg["payload"]["item"]
    location = msg["payload"]["location"]

    print(
        f"[{SUBJECT_NAME}] Sending ITEM_QUERY_RESPONSE for '{item}' with location '{location}'",
        flush=True,
    )
    send_message(
        sender=SUBJECT_NAME,
        receiver=msg["sender"],  # <-- respond to specific subject instance
        msg_type="ITEM_QUERY_RESPONSE",
        payload={
            "item": item,
            "location": location,
        },
    )

    return receive_item_query  # Loop back to receive next query


# --- Execution Start ---
if __name__ == "__main__":
    run(receive_item_query)
