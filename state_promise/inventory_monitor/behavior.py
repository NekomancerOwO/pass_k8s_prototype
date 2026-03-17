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
def receive_inventory_promise():
    """
    Customer subject receives timeout promise from service desk
    """
    msg = fetch_message(
        {
            "sender": "inventory-system",
            "msg_type": ["PROMISE"],
        }
    )
    if msg:
        promise_payload = msg["payload"]["promise"]
        promise_type = PromiseType(promise_payload["type"])
        if promise_type != PromiseType.STATE:
            raise RuntimeError("Invalid Promise Received!")

        # Promise Assessment
        def promise_condition(assessment_value):
            condition = promise_payload["condition"]
            if assessment_value > condition:
                return True  # Promise Kept
            print(
                f"[{SUBJECT_NAME}] Promise Broken. Item count {assessment_value} <= {condition}",
                flush=True,
            )
            return False  # Promise Broken

        inventory_promise = Promise(condition=promise_condition)
        return request_item_count(inventory_promise)

    return receive_inventory_promise  # Retry if request times out


def request_item_count(inventory_promise):
    """
    Implementation of a send state.
    """
    print(f"[{SUBJECT_NAME}] Sending item count request ...", flush=True)
    send_message(
        sender=SUBJECT_NAME,
        receiver="inventory-system",
        msg_type="REQUEST",
        payload="item_count_request",
    )
    return receive_item_count(inventory_promise)


def receive_item_count(inventory_promise):
    """
    Customer subject receives timeout promise from service desk
    """
    msg = fetch_message(
        {
            "sender": "inventory-system",
            "msg_type": ["RESPONSE"],
        }
    )
    if msg:
        count = msg["payload"]
        print(f"[{SUBJECT_NAME}] Item Count Received = {count}", flush=True)
        promise_state = inventory_promise.assess(count)
        if promise_state == PromiseState.KEPT:
            time.sleep(5)
            return request_item_count(inventory_promise)  # Continue Monitoring
        if promise_state == PromiseState.BROKEN:
            return request_item_delivery(count)  # Continue Behavior

    return receive_item_count(inventory_promise)  # Retry if no response


def request_item_delivery(count):
    """
    Implementation of a send state.
    """
    print(f"[{SUBJECT_NAME}] Sending item delivery request ...", flush=True)
    send_message(
        sender=SUBJECT_NAME,
        receiver="inventory-system",
        msg_type="UPDATE",
        payload=count + 200,
    )
    return end_state()


def end_state():
    print(f"[{SUBJECT_NAME}] Reached END state. Stopping subject behavior.", flush=True)
    while True:
        if termination_requested():
            print(f"[{SUBJECT_NAME}] PASS end state reached, terminating", flush=True)
            return None
        time.sleep(5)


# --- Execution Start ---
if __name__ == "__main__":
    run(receive_inventory_promise)
