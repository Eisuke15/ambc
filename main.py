import os
from subprocess import TimeoutExpired, run

from config import (BINARIES_DIR, EXECUTION_TIME_LIMIT, PCAP_DIR,
                    POST_EXECUTION_TIME, PRE_EXECUTION_TIME)
from maliciousfile import MaliciousFile
from ssh import send_and_execute_file
from tcpdump import Tcpdump
from vm import VM


def execute_file(filepath):
    """ファイルを実行する。

    EXECUTION_TIMEが経過した場合、実行を終了し、TimeoutExpiredをキャッチする。
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
    filepaths = [os.path.join(BINARIES_DIR, f) for f in os.listdir(BINARIES_DIR)]
    unique_file_set = set(MaliciousFile(filepath) for filepath in filepaths if os.path.isfile(filepath))

    # for f in unique_file_set:
    #     pcap_name = os.path.join(PCAP_DIR, os.path.basename(f.filepath)) + ".pcap"
    #     with TcpdumpWithSpareTime(pcap_name, PRE_EXECUTION_TIME, POST_EXECUTION_TIME):
    #         print(f"executing {f.filepath}")
    #         print(execute_file(f.fullpath()))
    #     sleep(3)  # tcpdumpの標準出力を追い越さないように余裕を持って次の実行へ
    #     print()

    file = list(unique_file_set)[0]
    with VM("ubuntu20.04", "clone-ubuntu") as vm:
        pcap_path = os.path.join(PCAP_DIR, os.path.basename(file.filepath) + ".pcap")
        with Tcpdump(pcap_path, vm.interface_name, PRE_EXECUTION_TIME, POST_EXECUTION_TIME):
            stdout, stderr = send_and_execute_file(file.fullpath(), vm.ip_addr)
            print(f"\n*****************stdout******************\n{stdout}\n")
            print(f"\n*****************stderr******************\n{stderr}\n")

    print("Done!")
