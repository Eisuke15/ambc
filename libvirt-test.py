import libvirt
import sys

try:
    conn = libvirt.openReadOnly(None)
except libvirt.libvirtError:
    print("Failed to open connection to the hypervisor")
    sys.exit(1)

dom = conn.lookupByName("ubuntu20.04")
print(dom.ID(), dom.OSType(), dom.info(), dom)