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
    return pcap_dir


def interactive_vm(local_specimen_path):
    stop_stp()
    vm = VM("ubuntu20.04", "clone-ubuntu")
    vm.__enter__()
    with SSH(vm.ip_addr, VM_USER_NAME, KEYFILE_PATH) as ssh:
        remote_specimen_path = f"/home/{VM_USER_NAME}/{os.path.basename(local_specimen_path)}"
        ssh.send_file(local_specimen_path, remote_specimen_path)
    return


def behavior_collection():
    """挙動収集の一連の動作の反復"""

    stop_stp()

    pcap_dir = mk_pcap_dir()

    while True:
        print(datetime.now())

        # まず検体をハニーポットから転送
        with SSH(HONEYPOT_IP_ADDR, HONEYPOT_USER_NAME, KEYFILE_PATH, HONEYPOT_SSH_PORT) as ssh:
            local_specimen_path, honeypot_specimen_path = ssh.wait_until_receive(TMP_SPECIMEN_DIR, HONEYPOT_SPECIMEN_DIR)

        if os.path.getsize(local_specimen_path):  # ファイルが空の場合はVMを建てない
            # Tcpdumpを開始しVM内で実行
            with VM("ubuntu20.04", "clone-ubuntu") as vm:
                pcap_path = os.path.join(pcap_dir, os.path.basename(local_specimen_path) + ".pcap")
                with Tcpdump(pcap_path, vm.interface_name, PRE_EXECUTION_TIME):
                    with SSH(vm.ip_addr, VM_USER_NAME, KEYFILE_PATH) as ssh:
                        vm_home_dir = f"/home/{VM_USER_NAME}"
                        remote_specimen_path = os.path.join(vm_home_dir, os.path.basename(local_specimen_path))
                        ssh.send_file(local_specimen_path, remote_specimen_path)
                        ssh.execute_file(remote_specimen_path, EXECUTION_TIME_LIMIT)
        else:
            print(f"{os.path.basename(local_specimen_path)}のサイズは0です。")

        # 最後に検体をハニーポットから削除
        with SSH(HONEYPOT_IP_ADDR, HONEYPOT_USER_NAME, KEYFILE_PATH, HONEYPOT_SSH_PORT) as ssh:
            ssh.remove_specimen(honeypot_specimen_path)

        print("\n\n\n")


if __name__ == "__main__":

    if len(sys.argv) == 2:
        interactive_vm(sys.argv[1])

    else:
        behavior_collection()
