import os

from config import BINARIES_DIR, PCAP_DIR, PRE_EXECUTION_TIME
from ssh import send_and_execute_file
from tcpdump import Tcpdump
from vm import VM

if __name__ == "__main__":

    files = []
    for item in os.listdir(BINARIES_DIR):
        path = os.path.join(BINARIES_DIR, item)
        # ディレクトリではなくファイル、かつサイズが0ではないファイルを抽出
        if os.path.isfile(path) and os.path.getsize(path):
            files.append(path)

    for file in files:
        with VM("ubuntu20.04", "clone-ubuntu") as vm:
            pcap_path = os.path.join(PCAP_DIR, os.path.basename(file) + ".pcap")
            with Tcpdump(pcap_path, vm.interface_name, PRE_EXECUTION_TIME):
                send_and_execute_file(file, vm.ip_addr)

    print("Done!")
