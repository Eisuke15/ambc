import os
from dotenv import load_dotenv

load_dotenv('.env')

PCAP_BASE_DIR = os.environ.get("PCAP_BASE_DIR")
PRE_EXECUTION_TIME = int(os.environ.get("PRE_EXECUTION_TIME"))
EXECUTION_TIME_LIMIT = int(os.environ.get("EXECUTION_TIME_LIMIT"))
VM_USER_NAME = os.environ.get("VM_USER_NAME")
KEYFILE_PATH = os.environ.get("KEYFILE_PATH")
HONEYPOT_USER_NAME = os.environ.get("HONEYPOT_USER_NAME")
