import sys


def die(msg: str, err: Exception):
    """任意のエラーメッセージを出力してプログラムを終了する。"""

    print(f"{msg}: {err}", file=sys.stderr)
    sys.exit(1)
