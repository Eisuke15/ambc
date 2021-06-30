import os
from subprocess import Popen, TimeoutExpired, run
from time import sleep

from config import BINARIES_DIR, EXECUTION_TIME, PCAP_DIR


class Tcpdump:
    """ with文を用いて確実にtcpdumpを開始・終了するためのクラス

    Attributes:
        filename (string): パケットデータのファイル名
        path (string): 実行するファイルのファイルパス
    """

    def __init__(self, binary_path):
        self.pcap_filepath = os.path.join(PCAP_DIR, os.path.basename(binary_path)) + ".pcap"
        self.path = binary_path
        self.proc = None

    def __enter__(self):
        print("**********start tcpdump**********")
        self.proc = Popen(["tcpdump", "-w", self.pcap_filepath], text=True)
        sleep(2)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sleep(2)  # sleepしないとtcpdumpが起動する前にファイルが実行されてパケットキャプチャが終了してしまう
        self.proc.terminate()
        sleep(2)
        print("**********stop tcpdump**********\n")

    def execute(self):
        return execute_file(self.path)


def execute_file(filepath):
    """ファイルを実行する。

    EXECUTION_TIMEが経過した場合、実行を終了し、TimeoutExpiredをキャッチする。

    Args:
        filepath (string): 実行するファイルのフルパス

    Returns:
        CompletedProcess: 実行結果
        TimeoutExpired: タイムアウトエラー

    """

    # 実行権限を与える
    os.chmod(filepath, 0o755)

    try:
        # checkをTrueにすると、コマンドが異常終了した際、runが例外SubprocessErrorを投げるようになる。
        # capture_outputをTrueにすると返り値のクラスに標準出力、標準エラー出力が格納される。
        # shell=Trueにすると文字列をそのままシェルに渡す。Falseの場合PATHに登録された実行ファイルでないといけない。
        # text=Trueにすると出力結果を文字列にエンコードする。
        result = run(filepath, shell=True, capture_output=True, check=False, text=True, timeout=EXECUTION_TIME)
        return result
    except TimeoutExpired as e:
        return e


if __name__ == "__main__":
    binaries = [os.path.join(BINARIES_DIR, f) for f in os.listdir(BINARIES_DIR) if os.path.isfile(os.path.join(BINARIES_DIR, f))]

    for binary in binaries:
        with Tcpdump(binary) as tcpdump:
            print(tcpdump.execute())

    print("Done!")
