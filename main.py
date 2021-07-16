import os
from subprocess import TimeoutExpired, run
from time import sleep

from config import (BINARIES_DIR, EXECUTION_TIME_LIMIT, PCAP_DIR,
                    POST_EXECUTION_TIME, PRE_EXECUTION_TIME)
from tcpdump import Tcpdump


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
        result = run(filepath, shell=True, capture_output=True, check=False, text=True, timeout=EXECUTION_TIME_LIMIT)
        return result
    except TimeoutExpired as e:
        return e


if __name__ == "__main__":
    binaries = [os.path.join(BINARIES_DIR, f) for f in os.listdir(BINARIES_DIR) if os.path.isfile(os.path.join(BINARIES_DIR, f))]

    with open("log.txt", mode="w") as f:
        for binary in binaries:
            print("**********start tcpdump**********")
            with Tcpdump(os.path.join(PCAP_DIR, os.path.basename(binary)) + ".pcap") as tcpdump:
                print(f"sleeping {PRE_EXECUTION_TIME} seconds")
                sleep(PRE_EXECUTION_TIME)
                print(f"executing {binary}")
                print(execute_file(binary), file=f)
                print("", file=f)
                print(f"sleeping {POST_EXECUTION_TIME} seconds")
                sleep(POST_EXECUTION_TIME)
            print("**********stop tcpdump**********")
            sleep(5)  # tcpdumpの出力を得るために余裕を持って次の実行へ
            print()

    print("Done!")
