import os
from subprocess import run

from config import BINARIES_DIR, EXECUTION_TIME


def execute_binary(binary_path):
    """バイナリファイルを実行する。

    EXECUTION_TIMEを

    Args:
        path (string): 実行するバイナリのフルパス

    Returns:
        CompletedProcess: 実行結果

    Todo:
        非同期にコマンド実行することで、実行時間も含めて時間を指定できるようにしたい。
    """

    # 実行権限を与える
    os.chmod(binary_path, 0o755)

    # checkをTrueにするとrunが例外SubprocessErrorを投げるようになる。
    # capture_outputをTrueにすると返り値のクラスに標準出力、標準エラー出力が格納される。
    # shell=Trueにすると文字列をそのままシェルに渡す。Falseの場合PATHに登録された実行ファイルでないといけない。
    # text=Trueにすると出力結果を文字列にエンコードする。
    result = run(binary_path, shell=True, capture_output=True, check=False, text=True, timeout=EXECUTION_TIME)
    return result


if __name__ == "__main__":
    binaries = [os.path.join(BINARIES_DIR, f) for f in os.listdir(BINARIES_DIR) if os.path.isfile(os.path.join(BINARIES_DIR, f))]

    for binary in binaries:
        print(execute_binary(binary))

    print("Done!")
