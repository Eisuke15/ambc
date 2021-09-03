import paramiko
from config import KEYFILE_PATH, VM_USER_NAME
import sys
import os

def send_and_execute_file(filepath):
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
        client.connect("192.168.122.184", username=VM_USER_NAME, key_filename=KEYFILE_PATH, timeout=5)
        
        try:
            sftp_connection = client.open_sftp()
            sftp_connection.put(filepath, f'/home/{VM_USER_NAME}/{filename}')
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

        _, stdout, stderr = client.exec_command(f"bash {filename}")
        stdout_text = stdout.read().decode()
        stderr_text = stderr.read().decode()

        return stdout_text, stderr_text


if __name__ == "__main__":
    print(send_and_execute_file("/home/denjo/test"))