from subprocess import Popen
from time import sleep


class Tcpdump:
    """ with文を用いて確実にtcpdumpを開始・終了するためのクラス"""

    def __init__(self, pcap_filepath):
        self.pcap_filepath = pcap_filepath
        self.proc = None

    def __enter__(self):
        self.proc = Popen(["tcpdump", "-w", self.pcap_filepath], text=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.proc.terminate()


class TcpdumpWithSpareTime(Tcpdump):
    """パケットキャプチャ前後に待ち時間を設定できるクラス"""

    def __init__(self, pcap_filepath, pre_execution_time, post_execution_time):
        super().__init__(pcap_filepath)
        self.pre_execution_time = pre_execution_time
        self.post_execution_time = post_execution_time

    def __enter__(self):
        res = super().__enter__()
        sleep(self.pre_execution_time)
        return res

    def __exit__(self, *args, **kwargs):
        sleep(self.post_execution_time)
        return super().__exit__(*args, **kwargs)
