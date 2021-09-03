import sys
from subprocess import run, CalledProcessError

import libvirt


class VM:
    """バーチャルマシンを管理するクラス"""

    def __init__(self, old_domain_name, new_domain_name):
        self.domain_name = new_domain_name
        self._clone_vm(old_domain_name, new_domain_name)
        self.conn = self._connect_qemu_hypervisor()
        self.dom = self.conn.lookupByName(old_domain_name)

        self.interface_name, self.ip_addr, self.mac_addr = self._get_interfaces()

    def _connect_qemu_hypervisor(self):
        """qemuハイパーバイザに接続する。

        Returns:
            conn (virConnect): QEMUへのコネクション
        """
        try:
            conn = libvirt.open("qemu:///system")
        except libvirt.libvirtError:
            print("ハイパーバイザに接続できませんでした。")
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
            print(e)
            sys.exit(1)

        return

    def _get_interfaces(self):
        """インターフェースにまつわる情報を返す

        Returns:
            ip : ip address
            mac: mac address
            interface_name: 仮想ブリッジのVMに繋げたネットワークインターフェース名
        """

        interface_name, addr_info = self.dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE, 0)
        # １つ目の謎の引数についてはここに詳細あり
        # https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainInterfaceAddressesSource

        ip = addr_info['addrs'][0]['addr']
        mac = addr_info['hwaddr']

        return ip, mac, interface_name
