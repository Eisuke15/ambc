import os
import sys
from datetime import datetime
from subprocess import run

from settings import (EXECUTION_TIME_LIMIT, HONEYPOT_IP_ADDR,
                      HONEYPOT_SPECIMEN_DIR, HONEYPOT_SSH_PORT,
                      HONEYPOT_USER_NAME, KEYFILE_PATH, PCAP_BASE_DIR,
                      PRE_EXECUTION_TIME, TMP_SPECIMEN_DIR, VM_USER_NAME)
from ssh import SSH
from tcpdump import Tcpdump
from vm import VM


def stop_stp(bridge_name="virbr0"):
    """ブリッジのSTPを停止する"""

    run(["brctl", "stp", bridge_name, "off"], check=True)


def mk_pcap_dir():
    """pcapを格納するディレクトリを作成

    実行日時を名前とする
    """
    pcap_dir_name = datetime.now().strftime("%Y-%m-%d-%H-%M")
    pcap_dir = os.path.join(PCAP_BASE_DIR, pcap_dir_name)
    os.mkdir(pcap_dir)
    return pcap_dir_name


def interactive_vm(local_specimen_path):
    stop_stp()
    vm = VM("ubuntu20.04", "clone-ubuntu")
    vm.__enter__()
    with SSH(vm.ip_addr, VM_USER_NAME, KEYFILE_PATH) as ssh:
        remote_specimen_path = f"/home/{VM_USER_NAME}/{os.path.basename(local_specimen_path)}"
        ssh.send_file(local_specimen_path, remote_specimen_path)
    return


def behavior_collection():
    """挙動収集の一連の動作"""

    stop_stp()

    # まず検体をハニーポットから転送
    with SSH(HONEYPOT_IP_ADDR, HONEYPOT_USER_NAME, KEYFILE_PATH, HONEYPOT_SSH_PORT) as ssh:
        local_specimen_path = ssh.wait_until_receive(TMP_SPECIMEN_DIR, HONEYPOT_SPECIMEN_DIR)

    pcap_dir = mk_pcap_dir()

    # Tcpdumpを開始しVM内で実行
    with VM("ubuntu20.04", "clone-ubuntu") as vm:
        pcap_path = os.path.join(pcap_dir, os.path.basename(local_specimen_path) + ".pcap")
        with Tcpdump(pcap_path, vm.interface_name, PRE_EXECUTION_TIME):
            with SSH(vm.ip_addr, VM_USER_NAME, KEYFILE_PATH) as ssh:
                vm_home_dir = f"/home/{VM_USER_NAME}"
                ssh.send_file(local_specimen_path, vm_home_dir)
                ssh.execute_file(vm_home_dir, EXECUTION_TIME_LIMIT)


if __name__ == "__main__":

    if len(sys.argv) == 2:
        interactive_vm(sys.argv[1])

    else:
        while True:
            print(datetime.now())
            behavior_collection()
            print("\n\n\n")
