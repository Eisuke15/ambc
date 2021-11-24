import libvirt
import sys

try:
    conn = libvirt.open("qemu:///system")
except libvirt.libvirtError as e:
    print(f"ハイパーバイザに接続できませんでした。{e}", file=sys.stderr)
    sys.exit(1)

domain = conn.lookupByName("ubuntu20.04")
print(domain.snapshotListNames())
print(domain.hasCurrentSnapshot())
print(domain.snapshotCurrent())
print(domain.snapshotCurrent().getName())
domain.revertToSnapshot(domain.snapshotLookupByName("snapshot1"), flags=libvirt.VIR_DOMAIN_SNAPSHOT_REVERT_RUNNING)
print(domain.snapshotCurrent().getName())
