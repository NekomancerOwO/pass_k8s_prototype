# pass_runtime/engine.py
import time


def run(start_state, delay=2):
    time.sleep(delay)  # Wait for input pool to initialize
    current_state = start_state

    while current_state:
        current_state = current_state()
