import os
import time

from runtime.config import INSTANCE_IP, SUBJECT_NAME
from runtime.messaging import fetch_message, send_message
from runtime.state_engine import run

subject_name = os.environ.get("SUBJECT_NAME", "example-subject")

# --- Subject Behavior ---


def receive_job_from_manager():
    """
    The warehouse worker waits for a job from the manager.
    """
    msg = fetch_message(
        {
            "sender": ["warehouse-manager"],
            "msg_type": ["JOB"],
        }
    )

    if msg:
        print(
            f"[{SUBJECT_NAME}] Received job for item '{msg['payload']['item']}' (order {msg['payload']['order_id']}) from {msg['sender']}",
            flush=True,
        )
        return send_to_warehouse_database(msg)

    return receive_job_from_manager  # Retry if request times out


def send_to_warehouse_database(msg):
    """
    The worker asks the warehouse database where the item is located.
    """
    item = msg["payload"]["item"]
    order_id = msg["payload"]["order_id"]

    print(
        f"[{SUBJECT_NAME}] Sending ITEM_QUERY for '{item}' (order {order_id}) to warehouse database",
        flush=True,
    )
    send_message(
        sender=INSTANCE_IP,  # <-- Send specific instance IP so response can be sent back to the same subject instance
        receiver="warehouse-database",
        msg_type="ITEM_QUERY",
        payload={
            "item": item,
        },
    )

    return receive_item_location(msg)


def receive_item_location(msg):
    """
    The worker waits for the warehouse database to respond with the item location.
    """
    order_id = msg["payload"]["order_id"]
    item = msg["payload"]["item"]

    response = fetch_message(
        {
            "sender": ["warehouse-database"],
            "msg_type": ["ITEM_QUERY_RESPONSE"],
        }
    )

    if response:
        location = response["payload"]["location"]
        print(
            f"[{SUBJECT_NAME}] Received location '{location}' for item '{item}' (order {order_id})",
            flush=True,
        )

        msg["payload"]["location"] = location
        return get_item_from_shelf(msg)

    return receive_item_location(msg)  # Retry if no response yet


def get_item_from_shelf(msg):
    """
    The worker physically retrieves the item.
    """
    item = msg["payload"]["item"]
    location = msg["payload"]["location"]

    print(
        f"[{SUBJECT_NAME}] Fetching item '{item}' from isle {location}...", flush=True
    )
    time.sleep(3)  # simulate time to fetch

    return send_item_to_shipping(msg)


def send_item_to_shipping(msg):
    """
    The worker sends the item along with order number to the shipping manager.
    """
    order_id = msg["payload"]["order_id"]
    item = msg["payload"]["item"]

    print(
        f"[{SUBJECT_NAME}] Sending item '{item}' (order {order_id}) to shipping manager",
        flush=True,
    )
    send_message(
        sender=SUBJECT_NAME,
        receiver="shipping-manager",
        msg_type="ITEM",
        payload={
            "order_id": order_id,
            "item": item,
        },
    )

    return receive_job_from_manager  # Ready to receive another job


# --- Execution Start ---
if __name__ == "__main__":
    run(receive_job_from_manager)
