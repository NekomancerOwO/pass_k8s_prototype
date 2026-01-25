import random
import socket
import time

import requests

from runtime.config import SUBJECT_NAME
from runtime.lifecycle import termination_requested

# --- Communication with Services ---


def fetch_message(criteria):
    """
    Helper function for communication with the Input Pool
    """
    try:
        response = requests.post(
            "http://localhost:8081/messages/receive", json=criteria, timeout=10
        )

        if response.status_code == 200:
            return response.json()

        if response.status_code == 408:
            return None

        print(f"[{SUBJECT_NAME}] Unexpected status: {response.status_code}", flush=True)

    except requests.exceptions.RequestException as e:
        print(f"[{SUBJECT_NAME}] Connection error: {e}", flush=True)
        time.sleep(2)

    return None


def send_message(
    sender: str,
    receiver: str,
    msg_type: str,
    payload,
    retry_delay=5,
):
    """
    Helper function for sending messages to other subjects. Will retry if message exchange fails.
    """

    message = {
        "sender": sender,
        "receiver": receiver,
        "msg_type": msg_type,
        "payload": payload,
    }

    url = f"http://{receiver}:8080/messages"

    while True:
        try:
            response = requests.post(url, json=message, timeout=5)

            if response.status_code == 200:
                print(f"[{sender}] Sent {msg_type} to {receiver}", flush=True)
                return True

            print(
                f"[{sender}] Send failed with status {response.status_code}",
                flush=True,
            )

        except requests.exceptions.RequestException as e:
            print(
                f"[{sender}] ERROR: Could not reach {receiver}. ({e})",
                flush=True,
            )
        time.sleep(retry_delay)
        if termination_requested():
            print(f"[{sender}] Send aborted due to termination request", flush=True)
            return False
        print(f"[{sender}] Retrying...", flush=True)


# --- Communication with headless Services ---


def discover_peers(service_name: str):
    """
    Returns a list of all Pod IPs associated with a headless service.
    """
    try:
        _, _, ips = socket.gethostbyname_ex(service_name)
        return ips
    except socket.gaierror:
        print(f"[{SUBJECT_NAME}] WARNING: Could not resolve service {service_name}")
        return []


def headless_send_message_all(sender: str, receiver: str, msg_type: str, payload):
    """
    Send message to every subject instance behind a headless service.
    """
    peers = discover_peers(receiver)
    results = []
    for ip in peers:
        success = send_message(sender, ip, msg_type, payload)
        results.append(success)
    return results


def headless_send_message_n(
    sender: str, receiver: str, msg_type: str, payload, count: int
):
    """
    Send message to exactly 'n' subject instances behind a headless service.
    """
    peers = discover_peers(receiver)

    if not peers:
        return False

    # Using random.sample to arbitrarily route messages without duplicates. Sends to all if n > available subjects
    targets = random.sample(peers, min(len(peers), count))

    results = []
    for ip in targets:
        success = send_message(sender, ip, msg_type, payload)
        results.append(success)
    return all(results)


def headless_send_message(
    sender: str,
    receiver: str,
    msg_type: str,
    payload,
):
    """
    Send a message to a single subject instance behind a headless Service
    """
    headless_send_message_n(sender, receiver, msg_type, payload, 1)
