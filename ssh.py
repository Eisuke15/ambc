import os
import socket
import sys
import threading
from time import sleep

import paramiko

from config import EXECUTION_TIME_LIMIT, KEYFILE_PATH, VM_USER_NAME


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

        try:
            sftp_connection = client.open_sftp()
            vm_path = f'/home/{VM_USER_NAME}/{filename}'
            sftp_connection.put(filepath, vm_path)
            sftp_connection.chmod(vm_path, 0o755)
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

        print(f"command: ./{filename}")

        thread = threading.Thread(target=execution_time_limit, args=(EXECUTION_TIME_LIMIT,))
        thread.start()

        try:
            _, stdout, stderr = client.exec_command(f"./{filename}", timeout=EXECUTION_TIME_LIMIT)

            print("****************stdout*****************")
            for line in stdout:
                print(line, end="")

            print("****************stderr*****************")
            for line in stderr:
                print(line, end="")
        except socket.timeout:
            print("実行時間制限に達しました。")
        finally:
            thread.join()


def execution_time_limit(time):
    sleep(time)


if __name__ == "__main__":
    send_and_execute_file("/home/denjo/testfiles2/test.sh", "192.168.122.184")
