import hashlib
import logging
import os
import sys
from datetime import datetime
from subprocess import PIPE, run

from paramiko.ssh_exception import SSHException

from settings import (EXECUTION_TIME_LIMIT, HONEYPOT_IP_ADDR,
                      HONEYPOT_SPECIMEN_DIRS, HONEYPOT_SSH_PORT,
                      HONEYPOT_USER_NAME, KEYFILE_PATH, LOGGING_DIR,
                      PCAP_BASE_DIR, PRE_EXECUTION_TIME, SPECIMEN_BASE_DIR)
from ssh import SSH
from tcpdump import Tcpdump
from vm import VM


def stop_stp(bridge_name="virbr0"):
    """ブリッジのSTPを停止する"""

    run(["brctl", "stp", bridge_name, "off"], check=True)


def calcurate_hash(local_specimen_path):
    """ファイルのハッシュ値を計算する"""

    with open(local_specimen_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def mk_datetime_dir(base_dir):
    """実行日時を名前とするディレクトリを作成"""
    dir_name = datetime.now().strftime("%Y-%m-%d-%H-%M")
    created_dir = os.path.join(base_dir, dir_name)
    os.mkdir(created_dir)
    return created_dir


def judge_os(local_specimen_path, filehash_set):
    """ファイル形式から、実行環境のOSを判定

    攻撃者が何度も同じ検体を送信する可能性を考慮し、
    一度実行したファイルは重複しないよう破棄する。

    Returns:
        Windowsか否か
        クローン元の仮想マシンのドメインネーム,
        仮想マシンのユーザ名

        実行する必要がないと判断するときはNoneを返す
    """

    filename = os.path.basename(local_specimen_path)
    filehash = calcurate_hash(local_specimen_path)
    if filehash in filehash_set:
        logging.info(f"{filename}は実行済みのためスルー")
        return None, None, None
    else:
        filehash_set.add(filehash)

    result = run(["file", local_specimen_path], check=False, text=True, stdout=PIPE)
    logging.info(f"ファイル形式:  {result.stdout}")
    tokens = result.stdout.split()
    if 'HTML' in tokens or 'SGML' in tokens or '(DLL)' in tokens:
        logging.info('ファイルを破棄')
        return None, None, None
    elif 'PE32' in tokens:
        logging.info("windowsで実行")
        return True, 'win10_32bit', 'malwa'
    elif 'ELF' in tokens or 'Bourne-Again' in tokens or 'Perl' in tokens or 'POSIX' in tokens:
        logging.info("Linuxで実行")
        return False, 'ubuntu20.04', 'vmuser'
    elif 'ASCII' in tokens:
        with open(local_specimen_path) as f:
            firstline = f.readline()
            secondline = f.readline()
        if firstline.startswith("root") and not secondline:
            logging.info("ファイルを破棄")
            return None, None, None
        else:
            logging.info("Linuxで実行")
            return False, 'ubuntu20.04', 'vmuser'
    else:
        logging.info('ファイルを破棄')
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

    pcap_dir = mk_datetime_dir(PCAP_BASE_DIR)
    specimen_dir = mk_datetime_dir(SPECIMEN_BASE_DIR)

    logging.info("start behaviour collection")

    # はじめにVMをすべて起動
    VM.start_if_shutoff("win10_32bit")
    VM.start_if_shutoff("ubuntu20.04")

    filehash_set = set()

    while True:
        try:
            # まず検体をハニーポットから転送　Todo: 書き込み中のファイルを転送してしまう問題をどうするか
            with SSH(HONEYPOT_IP_ADDR, HONEYPOT_USER_NAME, KEYFILE_PATH, HONEYPOT_SSH_PORT) as ssh:
                local_specimen_path, honeypot_specimen_path = ssh.wait_until_receive(specimen_dir, HONEYPOT_SPECIMEN_DIRS)
                ssh.remove_specimen(honeypot_specimen_path)

            is_windows, domain_name, vm_username = judge_os(local_specimen_path, filehash_set)
            if domain_name is not None:
                # Tcpdumpを開始しVM内で実行
                with VM(domain_name) as vm:
                    pcap_path = os.path.join(pcap_dir, os.path.basename(local_specimen_path) + ".pcap")
                    # ip_addr, _, interface_name = vm.get_interfaces()
                    if is_windows:
                        ip_addr = '192.168.122.120'
                        interface_name = 'vnet1'
                    else:
                        ip_addr = '192.168.122.115'
                        interface_name = 'vnet0'
                    with Tcpdump(pcap_path, interface_name, PRE_EXECUTION_TIME):
                        with SSH(ip_addr, vm_username, KEYFILE_PATH) as ssh:
                            remote_specimen_path = decide_remote_specimen_path(is_windows, local_specimen_path, vm_username)
                            ssh.send_file(local_specimen_path, remote_specimen_path)
                            ssh.execute_file(remote_specimen_path, EXECUTION_TIME_LIMIT)
        except EOFError as e:
            logging.error(f"pattern1: {e}が発生。挙動収集は続行。")
        except SSHException as e:
            logging.error(f"pattern2: {e}が発生。挙動収集は続行。")
        except Exception as e:
            logging.error(f"pattern3: {e}が発生。挙動収集は続行。")


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

    logging.basicConfig(
        filename=os.path.join(LOGGING_DIR, datetime.now().strftime("%Y-%m-%d-%H-%M.log")),
        format="%(levelname)s - %(asctime)s - %(message)s",
        level=logging.INFO
    )

    if len(sys.argv) == 2:
        interactive_vm(sys.argv[1])

    else:
        behavior_collection()
