import os
from dotenv import load_dotenv

load_dotenv('.env')

PCAP_BASE_DIR = os.environ.get("PCAP_BASE_DIR")
PRE_EXECUTION_TIME = int(os.environ.get("PRE_EXECUTION_TIME"))
EXECUTION_TIME_LIMIT = int(os.environ.get("EXECUTION_TIME_LIMIT"))
VM_USER_NAME = os.environ.get("VM_USER_NAME")
KEYFILE_PATH = os.environ.get("KEYFILE_PATH")
HONEYPOT_USER_NAME = os.environ.get("HONEYPOT_USER_NAME")
HONEYPOT_SSH_PORT = os.environ.get("HONEYPOT_SSH_PORT")
HONEYPOT_IP_ADDR = os.environ.get("HONEYPOT_IP_ADDR")
HONEYPOT_SPECIMEN_DIR = os.environ.get("HONEYPOT_SPECIMEN_DIR")
TMP_SPECIMEN_DIR = os.environ.get("TMP_SPECIMEN_DIR")
