import select
import socket
import sys
import pybonjour


regtype  = sys.argv[1]
timeout  = 5
queried  = []
resolved = []


def getaddrinfo_callback(sdRef, flags, interfaceIndex, errorCode, hostname,
                         address, ttl):
    if errorCode == pybonjour.kDNSServiceErr_NoError:
        print("address:", address)
        queried.append(True)


def resolve_callback(sdRef, flags, interfaceIndex, errorCode, fullname,
                     hosttarget, port, txtRecord):
    if errorCode != pybonjour.kDNSServiceErr_NoError:
        return

    print('Resolved service:')
    print('  fullname   =', fullname)
    print('  hosttarget =', hosttarget)
    print('  port       =', port)

    getaddrinfo_sdRef = \
        pybonjour.DNSServiceGetAddrInfo(interfaceIndex=interfaceIndex,
                                        hostname=hosttarget,
                                        callBack=getaddrinfo_callback)

    try:
        while not queried:
            ready = select.select([getaddrinfo_sdRef], [], [], timeout)
            if getaddrinfo_sdRef not in ready[0]:
                print('GetAddrInfo timed out')
                break
            pybonjour.DNSServiceProcessResult(getaddrinfo_sdRef)
        else:
            queried.pop()
    finally:
        getaddrinfo_sdRef.close()

    resolved.append(True)


def browse_callback(sdRef, flags, interfaceIndex, errorCode, serviceName,
                    regtype, replyDomain):
    if errorCode != pybonjour.kDNSServiceErr_NoError:
        return

    if not (flags & pybonjour.kDNSServiceFlagsAdd):
        print('Service removed')
        return

    print('Service added; resolving')

    resolve_sdRef = pybonjour.DNSServiceResolve(0,
                                                interfaceIndex,
                                                serviceName,
                                                regtype,
                                                replyDomain,
                                                resolve_callback)

    try:
        while not resolved:
            ready = select.select([resolve_sdRef], [], [], timeout)
            if resolve_sdRef not in ready[0]:
                print('Resolve timed out')
                break
            pybonjour.DNSServiceProcessResult(resolve_sdRef)
        else:
            resolved.pop()
    finally:
        resolve_sdRef.close()


browse_sdRef = pybonjour.DNSServiceBrowse(regtype = regtype,
                                          callBack = browse_callback)

try:
    try:
        while True:
            ready = select.select([browse_sdRef], [], [])
            if browse_sdRef in ready[0]:
                pybonjour.DNSServiceProcessResult(browse_sdRef)
    except KeyboardInterrupt:
        pass
finally:
    browse_sdRef.close()
