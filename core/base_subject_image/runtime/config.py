import os
import socket

SUBJECT_NAME = os.environ.get("SUBJECT_NAME", "name-not-found")
INSTANCE_IP = socket.gethostbyname(socket.gethostname())
