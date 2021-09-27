import os
import sys
import time
from datetime import datetime
from subprocess import run

from config import PCAP_BASE_DIR, PRE_EXECUTION_TIME
from ssh import connect_and_send_file, send_and_execute_file
from tcpdump import Tcpdump
from vm import VM


def interactive_vm(path):
    vm = VM("ubuntu20.04", "clone-ubuntu")
    vm.__enter__()
    connect_and_send_file(vm.ip_addr, path)
    return


def exec_all_specimen(path):

    # stpを停止
    run(["brctl", "stp", "virbr0", "off"], check=True, text=False)

    files = []
    for item in os.listdir(path):
        path = os.path.join(path, item)
        # ディレクトリではなくファイル、かつサイズが0ではないファイルを抽出
        if os.path.isfile(path) and os.path.getsize(path):
            files.append(path)

    pcap_dir_name = datetime.now().strftime("%Y-%m-%d-%H-%M")
    pcap_dir = os.path.join(PCAP_BASE_DIR, pcap_dir_name)
    os.mkdir(pcap_dir)

    start_time = time.time()
    for i, file in enumerate(files):
        elapsed_time = int(time.time() - start_time)
        print(f"\n{elapsed_time}[sec]  {i}/{len(files)}  {os.path.basename(file)}\n")
        with VM("ubuntu20.04", "clone-ubuntu") as vm:
            pcap_path = os.path.join(pcap_dir, os.path.basename(file) + ".pcap")
            with Tcpdump(pcap_path, vm.interface_name, PRE_EXECUTION_TIME):
                send_and_execute_file(file, vm.ip_addr)


if __name__ == "__main__":

    exec_content = sys.argv[1]

    if os.path.isfile(exec_content):
        interactive_vm(exec_content)

    elif os.path.isdir(exec_content):
        exec_all_specimen(exec_content)

    else:
        print("指定したパスが存在しません。", file=sys.stderr)
        sys.exit(1)
