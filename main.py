import os
import sys
from datetime import datetime
from subprocess import PIPE, run

from settings import (EXECUTION_TIME_LIMIT, HONEYPOT_IP_ADDR,
                      HONEYPOT_SPECIMEN_DIRS, HONEYPOT_SSH_PORT,
                      HONEYPOT_USER_NAME, KEYFILE_PATH, PCAP_BASE_DIR,
                      PRE_EXECUTION_TIME, TMP_SPECIMEN_DIR)
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


def judge_os(local_specimen_path):
    """ファイル形式から、実行環境のOSを判定

    Returns:
        Windowsか否か
        クローン元の仮想マシンのドメインネーム,
        仮想マシンのユーザ名

        実行する必要がないと判断するときはNoneを返す
    """

    result = run(["file", local_specimen_path], check=False, text=True, stdout=PIPE)
    print(f"ファイル形式:  {result.stdout}")
    tokens = result.stdout.split()
    if 'HTML' in tokens or 'SGML' in tokens or '(DLL)' in tokens:
        print('ファイルを破棄')
        return None, None, None
    elif 'PE32' in tokens:
        return True, 'win10_32bit', 'malwa'
    elif 'ELF' in tokens or 'Bourne-Again' in tokens or 'ASCII' in tokens or 'Perl' in tokens:
        return False, 'ubuntu20.04', 'vmuser'
    else:
        print('ファイルを破棄')
        return None, None, None


def decide_remote_specimen_path(is_windows, local_specimen_path, vm_username):
    filename = os.path.basename(local_specimen_path)
    if is_windows:
        return r"C:\Users" + '\\' + vm_username + '\\' + filename + '.exe'
    else:
        return os.path.join('/home', vm_username, filename)


def behavior_collection():
    """挙動収集の一連の動作の反復"""

    stop_stp()

    pcap_dir = mk_pcap_dir()

    while True:
        print(datetime.now())

        # まず検体をハニーポットから転送　Todo: 書き込み中のファイルを転送してしまう問題をどうするか
        with SSH(HONEYPOT_IP_ADDR, HONEYPOT_USER_NAME, KEYFILE_PATH, HONEYPOT_SSH_PORT) as ssh:
            local_specimen_path, honeypot_specimen_path = ssh.wait_until_receive(TMP_SPECIMEN_DIR, HONEYPOT_SPECIMEN_DIRS)

        is_windows, domain_name, vm_username = judge_os(local_specimen_path)
        if domain_name is not None:
            # Tcpdumpを開始しVM内で実行
            with VM(domain_name) as vm:
                pcap_path = os.path.join(pcap_dir, os.path.basename(local_specimen_path) + ".pcap")
                ip_addr, _, interface_name = vm.get_interfaces()
                with Tcpdump(pcap_path, interface_name, PRE_EXECUTION_TIME):
                    with SSH(ip_addr, vm_username, KEYFILE_PATH) as ssh:
                        remote_specimen_path = decide_remote_specimen_path(is_windows, local_specimen_path, vm_username)
                        ssh.send_file(local_specimen_path, remote_specimen_path)
                        ssh.execute_file(remote_specimen_path, EXECUTION_TIME_LIMIT)

        # 最後に検体をハニーポットから削除
        with SSH(HONEYPOT_IP_ADDR, HONEYPOT_USER_NAME, KEYFILE_PATH, HONEYPOT_SSH_PORT) as ssh:
            ssh.remove_specimen(honeypot_specimen_path)

        print("\n\n\n")


def interactive_vm(local_specimen_path):
    stop_stp()
    is_windows, domain_name, vm_username = judge_os(local_specimen_path)
    vm = VM(domain_name)
    vm.__enter__()
    ip_addr, *_ = vm.get_interfaces()
    with SSH(ip_addr, vm_username, KEYFILE_PATH) as ssh:
        remote_specimen_path = decide_remote_specimen_path(is_windows, local_specimen_path, vm_username)
        ssh.send_file(local_specimen_path, remote_specimen_path)
    return


if __name__ == "__main__":

    if len(sys.argv) == 2:
        interactive_vm(sys.argv[1])

    else:
        behavior_collection()
