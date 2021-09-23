import os
import sys
import xml.etree.ElementTree as ET
from subprocess import CalledProcessError, run
from time import sleep

import libvirt


class VM:
    """バーチャルマシンを管理するクラス"""

    def __init__(self, old_domain_name, new_domain_name):
        self.old_domain_name = old_domain_name
        self.new_domain_name = new_domain_name

    def __enter__(self):
        """with文に入るときに実行する。

        この内部でエラー発生しても__exit__ は実行されないので注意。
        """

        try:
            self._clone_vm(self.old_domain_name, self.new_domain_name)
        except KeyboardInterrupt:
            conn = self._connect_qemu_hypervisor()
            self.dom = conn.lookupByName(self.new_domain_name)
            conn.close()
            self._delete_imagefile_path()
            self._undefine()
            sys.exit(1)

        try:
            conn = self._connect_qemu_hypervisor()
            self.dom = conn.lookupByName(self.new_domain_name)
            conn.close()
            self._start_vm()
            self.ip_addr, _, self.interface_name = self._get_interfaces()  # macアドレスは現時点では必要ないので読み捨て
        except KeyboardInterrupt:
            self.__exit__()
            sys.exit(1)

        return self

    def __exit__(self, *args, **kwargs):
        """いかなる原因でも（エラー含めて）with文を抜けるときに確実に実行する"""

        self._destroy_vm()
        self._delete_imagefile_path()
        self._undefine()

    def _connect_qemu_hypervisor(self):
        """qemuハイパーバイザに接続する。

        Returns:
            conn (virConnect): QEMUへのコネクション
        """
        try:
            conn = libvirt.open("qemu:///system")
        except libvirt.libvirtError as e:
            print(f"ハイパーバイザに接続できませんでした。{e}", file=sys.stderr)
            sys.exit(1)

        return conn

    def _clone_vm(self, old_domain_name, new_domain_name):
        """新しいVMを用意する。

        毎回OSインストールするのは時間がかかるので、インストール済みの既存のVMをクローンする。

        Args:
            old_domain_name (str) : クローン元のVMのドメインネーム
            new_domain_name (str) : 作成するクローンのVMのドメインネーム
        """

        try:
            run(["virt-clone", "-o", old_domain_name, "-n", new_domain_name, "--auto-clone"], check=True, text=False)
        except CalledProcessError as e:
            print(f"VMのクローンに失敗しました。{e}", file=sys.stderr)
            sys.exit(1)
        return

    def _start_vm(self):
        """vmを起動する。"""

        if self.dom.create() < 0:
            print(f"{self.dom.name}を起動できません。", file=sys.stderr)
            sys.exit(1)

    def _destroy_vm(self):
        """VMを強制終了する。"""

        # そもそも起動していないなどのエラーをキャッチし終了
        try:
            result = self.dom.destroy()
        except libvirt.libvirtError as e:
            print(f"{self.new_domain_name}の強制終了に失敗しました。{e}", file=sys.stderr)
            sys.exit(1)

        # 強制終了操作はできるが失敗したときは通知のみ
        if result < 0:
            print(f"{self.new_domain_name}の強制終了に失敗しました。", file=sys.stderr)
        else:
            print(f"{self.new_domain_name}を強制終了")

    def _get_interfaces(self):
        """インターフェースにまつわる情報を返す

        Returns:
            ip : ip address
            mac: mac address
            interface_name: 仮想ブリッジのVMに繋げたネットワークインターフェース名
        """

        iface_info = None
        # vmが起動してからipアドレスが割り振られるまでの時間を待機
        while not iface_info:
            iface_info = self.dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE, 0)
            # １つ目の謎の引数についてはここに詳細あり
            # https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainInterfaceAddressesSource
            print("waiting for dhcp")
            sleep(5)

        interface_name = list(iface_info.keys())[0]
        addr_info = iface_info[interface_name]

        ip = addr_info['addrs'][0]['addr']
        mac = addr_info['hwaddr']

        return ip, mac, interface_name

    def _delete_imagefile_path(self):
        """ディスクイメージファイルを削除する"""

        xml = self.dom.XMLDesc()
        imagefile_path = ET.fromstring(xml).find("devices/disk/source").get("file")
        try:
            os.remove(imagefile_path)
        except TypeError:
            print(f"{self.new_domain_name}のディスクイメージの削除に失敗しました。", file=sys.stderr)
        else:
            print(f"{self.new_domain_name}のディスクイメージを削除しました。")

    def _undefine(self):
        """VMを削除する"""

        if self.dom.undefine() < 0:
            print(f"{self.new_domain_name}の削除に失敗しました。", file=sys.stderr)
        else:
            print(f"{self.new_domain_name}を削除しました。")


if __name__ == "__main__":
    vm = VM("ubuntu20.04", "clone")
    print(vm.ip_addr, vm.interface_name)
