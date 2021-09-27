import os
import socket
import sys
import threading
from time import sleep

import paramiko

from config import EXECUTION_TIME_LIMIT, KEYFILE_PATH, VM_USER_NAME


def send_file(client, filepath):
    """SFTPでファイルの送信"""

    filename = os.path.basename(filepath)
    try:
        sftp_connection = client.open_sftp()
        vm_path = f'/home/{VM_USER_NAME}/{filename}'
        sftp_connection.put(filepath, vm_path)
        sftp_connection.chmod(vm_path, 0o755)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)


def connect_and_send_file(ip_addr, filepath):
    with paramiko.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip_addr, username=VM_USER_NAME, key_filename=KEYFILE_PATH, timeout=1)
        send_file(client, filepath)


def send_and_execute_file(filepath, ip_addr):
    """ファイルを送信して実行し、結果を得るファイル。

    Args:
        filepath (str): 送信、実行するファイルのフルパス

    Returns:
        stdout_text: 標準出力をutf-8でデコードしたもの
        stderr_text: 標準エラー出力をutf-8でデコードしたもの
    """

    filename = os.path.basename(filepath)
    with paramiko.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip_addr, username=VM_USER_NAME, key_filename=KEYFILE_PATH, timeout=1)

        send_file(client, filepath)

        print(f"command: ./{filename}")

        # 別のスレッドで、実行時間制限だけsleepする関数を実行する。
        # これにより、もしexec_command関数で実行したコマンドが時間内に終了しても、
        # 制限時間までスレッドがjoinするのを待つことで毎回一定時間パケットキャプチャするようにしている。
        thread = threading.Thread(target=execution_time_limit, args=(EXECUTION_TIME_LIMIT,))
        thread.start()

        try:
            _, stdout, stderr = client.exec_command(f"./{filename}", timeout=EXECUTION_TIME_LIMIT)

            print("\n****************stdout*****************")
            for line in stdout:
                print(line, end="")

            print("\n****************stderr*****************")
            for line in stderr:
                print(line, end="")
        except socket.timeout:
            print("\n実行時間制限\n")
        else:
            returncode = stdout.channel.recv_exit_status()
            print(f"\n実行終了 return code = {returncode}\n")
        finally:
            thread.join()


def execution_time_limit(time):
    sleep(time)


if __name__ == "__main__":
    send_and_execute_file("/home/denjo/testfiles2/test.sh", "192.168.122.184")
