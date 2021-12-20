import logging
import os
import sys
import xml.etree.ElementTree as ET
from subprocess import CalledProcessError, run
from time import sleep

import libvirt

from util import die


class VM:
    """バーチャルマシンを管理するクラス"""

    def __init__(self, domain_name: str, clone: bool = False, new_domain_name: str = None, snapshot_name: str = "default_snapshot_for_revert"):
        """初期化

        Arguments:
            domain_name(str): 扱う仮想マシンのドメインネーム
            clone(bool): Trueの場合、実行環境はcloneによって用意する。Falseの場合はスナップショット機能で復元する
            new_domain_name(str): cloneの場合、クローン先の仮想マシンのドメインネーム
            snapshot_name(str): 作成するスナップショットの名前
        """
        self.domain_name = domain_name
        self.new_domain_name = new_domain_name
        self.clone = clone
        self.snapshot_name = snapshot_name

    def __enter__(self):
        """with文に入るときに実行する。

        この内部でエラー発生しても__exit__ は実行されないので注意。
        """

        with self.__connect_qemu_hypervisor() as conn:

            if self.clone:  # クローンによる実行環境の用意
                try:
                    self.__clone_vm(self.domain_name, self.new_domain_name)
                except KeyboardInterrupt:
                    # Todo: クローン中断の際にイメージファイル削除されていることを確かめる
                    self.dom = conn.lookupByName(self.new_domain_name)
                    self.__delete_imagefile()
                    self.__undefine()
                    sys.exit(1)
                else:
                    self.dom = conn.lookupByName(self.new_domain_name)
                    self.__start_vm()

            else:  # スナップショットによる実行環境の用意
                self.dom = conn.lookupByName(self.domain_name)
                self.snapshot = self.__get_or_create_snapshot(self.snapshot_name)
                # Windows Defenderは時間の経過により自動で起動してしまうため、ここで強制的に無効状態にリセットする
                self.__revert_to_snapshot()

        return self

    def __exit__(self, *args, **kwargs):
        """いかなる原因でも（エラー含めて）with文を抜けるときに確実に実行する"""

        if self.clone:
            self.__destroy_vm()
            self.__delete_imagefile()
            self.__undefine()
        else:
            self.__revert_to_snapshot()

    @classmethod
    def start_if_shutoff(cls, domain_name):
        """特定のドメイン名のVMが起動していない場合起動する。

        stateの詳細は下記
        https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainState
        """

        with libvirt.open("qemu:///system") as conn:
            domain = conn.lookupByName(domain_name)
            state = domain.info()[0]
            if state == 1:
                pass
            elif state == 5:
                domain.create()
            else:
                die("VMが起動中もしくは終了中である必要があります。")

    def __connect_qemu_hypervisor(self):
        """qemuハイパーバイザに接続する。

        Returns:
            conn (virConnect): QEMUへのコネクション
        """
        try:
            conn = libvirt.open("qemu:///system")
        except libvirt.libvirtError as e:
            die("ハイパーバイザに接続できませんでした", e)

        return conn

    def __create_snapshot(self, snapshot_name: str):
        """指定された名前のスナップショットを作成し、作成したスナップショットを返す"""

        xml_desc = f"""
        <domainsnapshot>
            <name>{snapshot_name}</name>
        </domainsnapshot>
        """
        logging.info(f'スナップショット"{snapshot_name}"を作成中')
        return self.dom.snapshotCreateXML(xmlDesc=xml_desc, flags=libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_ATOMIC)

    def __get_or_create_snapshot(self, snapshot_name: str):
        """指定された名前のスナップショットが存在しない場合、新規作成する"""

        if snapshot_name not in self.dom.snapshotListNames():
            logging.info(f"スナップショット'{snapshot_name}'を作成")
            return self.__create_snapshot(snapshot_name)
        else:
            logging.info(f"既存のスナップショット'{snapshot_name}'を利用")
            return self.dom.snapshotLookupByName(snapshot_name)

    def __revert_to_snapshot(self):
        """スナップショットの状態に復元する

        復元後のVMの状態は実行中であるよう指定している。
        """
        self.dom.revertToSnapshot(self.snapshot, flags=libvirt.VIR_DOMAIN_SNAPSHOT_REVERT_RUNNING)
        logging.info(f"スナップショット'{self.snapshot_name}'の状態に復元")

    def __clone_vm(self, old_domain_name, new_domain_name):
        """新しいVMを用意する。

        毎回OSインストールするのは時間がかかるので、インストール済みの既存のVMをクローンする。

        Args:
            old_domain_name (str) : クローン元のVMのドメインネーム
            new_domain_name (str) : 作成するクローンのVMのドメインネーム
        """

        try:
            logging.info(f"{old_domain_name}のクローン開始")
            run(["virt-clone", "-o", old_domain_name, "-n", new_domain_name, "--auto-clone", "-q"], check=True, text=False)
        except CalledProcessError as e:
            die("VMのクローンに失敗しました。", e)

        logging.info("クローンが正常に終了しました")
        return

    def __start_vm(self):
        """vmを起動する。"""

        try:
            self.dom.create()
        except libvirt.libvirtError as e:
            die(f"{self.dom.name()}を起動できません。", e)

    def __destroy_vm(self):
        """VMを強制終了する。"""

        # そもそも起動していないなどのエラーをキャッチし終了
        try:
            result = self.dom.destroy()
        except libvirt.libvirtError as e:
            die(f"{self.dom.name()}の強制終了に失敗しました.", e)

        # 強制終了操作はできるが失敗したときは通知のみ
        if result < 0:
            logging.warning(f"{self.dom.name()}の強制終了に失敗しました。", file=sys.stderr)
        else:
            logging.info(f"{self.dom.name()}を強制終了")

    def get_interfaces(self):
        """インターフェースにまつわる情報を返す

        Returns:
            ip : ip address
            mac: mac address
            interface_name: 仮想ブリッジのVMに繋げたネットワークインターフェース名
        """

        iface_info = None
        logging.info("IPアドレスを取得中")
        # vmが起動してからipアドレスが割り振られるまでの時間を待機
        while not iface_info:
            iface_info = self.dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE, 0)
            # １つ目の謎の引数についてはここに詳細あり
            # https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainInterfaceAddressesSource
            sleep(1)

        interface_name = list(iface_info.keys())[0]
        addr_info = iface_info[interface_name]

        ip = addr_info['addrs'][0]['addr']
        mac = addr_info['hwaddr']

        return ip, mac, interface_name

    def __delete_imagefile(self):
        """ディスクイメージファイルを削除する"""

        xml = self.dom.XMLDesc()
        imagefile_path = ET.fromstring(xml).find("devices/disk/source").get("file")
        try:
            os.remove(imagefile_path)
        except TypeError:
            logging.warning(f"{self.dom.name()}のディスクイメージの削除に失敗しました。", file=sys.stderr)
        else:
            logging.info(f"{self.dom.name()}のディスクイメージを削除しました。")

    def __undefine(self):
        """VMを削除する"""

        if self.dom.undefine() < 0:
            logging.info(f"{self.dom.name()}の削除に失敗しました。", file=sys.stderr)
        else:
            logging.info(f"{self.dom.name()}を削除しました。")
