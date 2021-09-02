import libvirt
import sys

try:
    conn = libvirt.open("qemu:///system")
except Exception as e:
    print("Failed to open connection to the hypervisor")
    exit(1)

print(conn.listInterfaces())
dom = conn.lookupByName("ubuntu20.04")
ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE, 0)
print(ifaces)
print(dom.ID(), dom.OSType(), dom.info(), dom)