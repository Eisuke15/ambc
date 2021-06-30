import os
from subprocess import run, TimeoutExpired

from config import BINARIES_DIR, EXECUTION_TIME


def execute_binary(binary_path):
    """バイナリファイルを実行する。

    EXECUTION_TIMEが経過した場合、実行を終了し、TimeoutExpiredをキャッチする。

    Args:
        path (string): 実行するバイナリのフルパス

    Returns:
        CompletedProcess: 実行結果
        TimeoutExpired: タイムアウトエラー

    """

    # 実行権限を与える
    os.chmod(binary_path, 0o755)

    try:
        # checkをTrueにすると、コマンドが異常終了した際、runが例外SubprocessErrorを投げるようになる。
        # capture_outputをTrueにすると返り値のクラスに標準出力、標準エラー出力が格納される。
        # shell=Trueにすると文字列をそのままシェルに渡す。Falseの場合PATHに登録された実行ファイルでないといけない。
        # text=Trueにすると出力結果を文字列にエンコードする。
        result = run(binary_path, shell=True, capture_output=True, check=False, text=True, timeout=EXECUTION_TIME)
        return result
    except TimeoutExpired as e:
        return e


if __name__ == "__main__":
    binaries = [os.path.join(BINARIES_DIR, f) for f in os.listdir(BINARIES_DIR) if os.path.isfile(os.path.join(BINARIES_DIR, f))]

    for binary in binaries:
        print(execute_binary(binary))

    print("Done!")
