import signal
import sys
import time

from flask import Flask, jsonify, request

from input_pool.config import POOL_SIZE, SENDER_LIMIT, STRATEGY, TYPE_LIMIT, Message
from input_pool.input_pool import InputPool

internal_app = Flask("internal")
external_app = Flask("external")
input_pool = InputPool(
    max_size=POOL_SIZE,
    per_sender_limit=SENDER_LIMIT,
    per_type_limit=TYPE_LIMIT,
    strategy=STRATEGY,
)


def handle_sigterm(signum, frame):
    print("[input-pool] SIGTERM received, shutting down", flush=True)
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_sigterm)


@internal_app.route("/messages/receive", methods=["POST"])
def receive():
    msg = input_pool.receive_blocking(request.json, timeout=9)
    if msg:
        return jsonify(msg.__dict__), 200
    return jsonify({"error": "timeout"}), 408


@external_app.route("/messages", methods=["POST"])
def post_message():
    msg = Message(**request.json, timestamp=time.time())
    if input_pool.add_message(msg):
        return jsonify({"status": "accepted"}), 200
    return jsonify({"status": "blocked"}), 429


def main():
    import threading

    t1 = threading.Thread(
        target=lambda: internal_app.run(
            host="127.0.0.1", port=8081, debug=False, use_reloader=False
        )
    )
    t2 = threading.Thread(
        target=lambda: external_app.run(
            host="0.0.0.0", port=8080, debug=False, use_reloader=False
        )
    )
    t1.start()
    t2.start()
    t1.join()
    t2.join()


if __name__ == "__main__":
    main()
