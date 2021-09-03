from subprocess import Popen
from time import sleep


class Tcpdump:
    """with文を用いて確実にtcpdumpを開始・終了するためのクラス"""

    def __init__(self, pcap_filepath, interface, pre_execution_time=0, post_execution_time=0):
        self.pcap_filepath = pcap_filepath
        self.proc = None
        self.interface = interface
        self.pre_execution_time = pre_execution_time
        self.post_execution_time = post_execution_time

    def __enter__(self):
        self.proc = Popen(["tcpdump", "-w", self.pcap_filepath, "-i", self.interface], text=True)
        sleep(self.pre_execution_time)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sleep(self.post_execution_time)
        self.proc.terminate()
