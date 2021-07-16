from subprocess import Popen


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
