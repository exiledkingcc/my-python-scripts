#!/usr/bin/env python3
# coding: utf-8

import asyncio
import logging
import ipaddress
import socket


log = logging.getLogger("lightproxy")


class LightProxyProtocol(asyncio.Protocol):

    CMD_CONN = 1
    CMD_BIND = 2
    CMD_UDPA = 3

    ATYPE_IPV4 = 1
    ATYPE_DOMN = 3
    ATYPE_IPV6 = 4

    def __init__(self, loop):
        self._loop = loop
        self._transport = None
        self._peername = None
        self._socket = None
        self._stage = None


    def connection_made(self, transport):
        self._transport = transport
        self._peername = self._transport.get_extra_info('peername')
        log.info("Connection from %s", self._peername)
        self._stage = 0

    def connection_lost(self, exc):
        log.info("Connection disconneted from %s", self._peername)
        self._loop.remove_reader(self._socket)
        self._socket.close()


    def data_received(self, data: bytes):
        if self._stage == 0:
            self._stage = 1
            self._handle_authorised(data)
        elif self._stage == 1:
            self._stage = 2
            self._handle_command(data)
        elif self._stage == 2:
            self._handle_connect(data)
        else:
            log.error("stage error")

    def _handle_authorised(self, data: bytes):
        self._transport.write(b"\x05\x00")

    def _handle_command(self, data: bytes):
        log.info("%s", data)
        ver = data[0]
        cmd = data[1]
        atype = data[3]
        addr = data[4:-2]
        port = data[-2:]
        if atype == self.ATYPE_IPV4 or atype == self.ATYPE_IPV6:
            host = addr.decode("ascii")
        elif atype == self.ATYPE_DOMN:
            host = addr[1:]
        else:
            log.error("no such atype: %d", atype)

        info = socket.getaddrinfo(host, self._port_b2i(port))[0]
        self._socket = socket.socket(info[0], info[1], info[2])
        self._socket.connect(info[-1])
        self._loop.add_reader(self._socket, self._recv)

        self._transport.write(b"\x05\x00" + data[2:])

    def _handle_connect(self, data: bytes):
        self._socket.sendall(data)


    def _recv(self):
        data = self._socket.recv(4096)
        if data:
            self._transport.write(data)


    @staticmethod
    def _port_b2i(bb: bytes):
        return int.from_bytes(bb, "big")

    @staticmethod
    def _port_i2b(ii: int):
        return ii.to_bytes(16, "big")


if __name__ == "__main__":
    import cclog
    cclog.init()
    loop = asyncio.get_event_loop()
    coro = loop.create_server(lambda: LightProxyProtocol(loop), '127.0.0.1', 22333)
    server = loop.run_until_complete(coro)
    try:
        loop.run_forever()
    except:
        pass
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()
