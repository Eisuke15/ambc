import os
import socket
import threading
from time import sleep

import paramiko

from util import die


class SSH:
    """with文でsshコネクションを管理する

    Attributes:
        ip_addr (str): 接続するサーバのIPアドレス
        username (str): 接続先のユーザ名
        key_file_path (str): 秘密鍵のパス
        port (str): 接続先するSSHサーバのポート（デフォルトは22）
    """

    def __init__(self, ip_addr, username, key_file_path, port=22):
        self.ip_addr = ip_addr
        self.username = username
        self.key_file_path = key_file_path
        self.port = port

    def __enter__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            hostname=self.ip_addr,
            username=self.username,
            key_filename=self.key_file_path,
            port=self.port
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()

    def send_file(self, local_specimen_path, remote_specimen_path):
        """SFTPでファイルの送信

        Args:
            local_specimen_path (str): 送信する検体のパス
            remote_specimen_path (str): 送信先のパス
        """

        with self.client.open_sftp() as sftp_conn:
            sftp_conn.put(local_specimen_path, remote_specimen_path)
            sftp_conn.chmod(remote_specimen_path, 0o755)

    def execute_file(self, remote_specimen_path, ovservation_time):
        """検体を実行し、VM上での検体の出力を出力しながら、一定時間待機する。

        Args:
            remote_specimen_path (str): 実行するファイルのパス
        """

        # 別のスレッドで、実行時間制限だけsleepする関数を実行する。
        # これにより、もしexec_command関数で実行したコマンドが時間内に終了しても、
        # 制限時間までスレッドがjoinするのを待つことで毎回一定時間パケットキャプチャするようにしている。
        def execution_time_limit(time):
            sleep(time)
        thread = threading.Thread(target=execution_time_limit, args=(ovservation_time,))
        thread.start()

        try:
            command = f"{remote_specimen_path} 2>&1"
            print(f"Command: {command}")
            _, stdout, stderr = self.client.exec_command(command, timeout=ovservation_time)

            print("\n****************出力*****************")
            for line in stdout:
                print(line, end="")

        except socket.timeout:
            print("\n実行時間制限\n")
        else:
            returncode = stdout.channel.recv_exit_status()
            print(f"\n実行終了 return code = {returncode}\n")
        finally:
            thread.join()
            print("パケット観測終了")

    def wait_until_receive(self, local_dir_path: str, remote_dir_paths):
        """指定されたパスを監視する．ファイルを発見したら受信して，そのパスを返す．

        Args:
            local_dir_path (str): 受信するローカルのディレクトリ
            remote_dir_paths (list(str)): 監視するリモートのディレクトリのリスト

        Returns:
            local_specimen_path (str): 受信したファイルのパス
            remote_specimen_path (str): 送信したファイルのパス

        Notes:
            remote_dir_pathに読み書き実行権限が必要
        """

        def find_specimen(remote_dir_paths):
            """指定されたパスを監視し、ファイルを発見したらパスを返す。何も存在しなければNoneを返す。"""

            for path in remote_dir_paths:
                specimen_list = sftpconn.listdir(path)
                if specimen_list:
                    return os.path.join(path, specimen_list[0])
            return None

        with self.client.open_sftp() as sftpconn:
            try:
                remote_specimen_path = find_specimen(remote_dir_paths)
            except IOError as e:
                die("指定した監視するディレクトリが存在しません。", e)
            if not remote_specimen_path:
                print("検体を待機中")
            while not remote_specimen_path:
                sleep(10)
                remote_specimen_path = find_specimen(remote_dir_paths)
            else:
                specimen_filename = os.path.basename(remote_specimen_path)
                print(f"Transferring {specimen_filename}")
                local_specimen_path = os.path.join(local_dir_path, specimen_filename)
                sftpconn.get(remote_specimen_path, local_specimen_path)
                return local_specimen_path, remote_specimen_path

    def remove_specimen(self, remote_specimen_path):
        """リモートのファイルを削除する"""

        with self.client.open_sftp() as sftp_conn:
            try:
                sftp_conn.remove(remote_specimen_path)
                print(f"ハニーポットの{remote_specimen_path}を削除しました。")
            except IOError as e:
                print(f"ハニーポットに{remote_specimen_path}が存在しないため、削除できません。: {e}")


if __name__ == "__main__":
    pass
