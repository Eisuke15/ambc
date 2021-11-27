import logging
import sys


def die(msg: str, err: Exception):
    """任意のエラーメッセージを出力してプログラムを終了する。"""

    logging.error(f"{msg}: {err}", file=sys.stderr)
    sys.exit(1)
