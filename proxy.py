#!/usr/bin/env python3
# coding: utf-8

import asyncio
import logging
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
        self._con_data = None
        self._futures = []


    def connection_made(self, transport):
        self._transport = transport
        self._peername = self._transport.get_extra_info('peername')
        log.info("connected from %s", self._peername)
        self._stage = 0

    def connection_lost(self, exc):
        log.info("disconneted from %s", self._peername)
        if self._socket:
            self._loop.remove_reader(self._socket)
            self._socket.close()
        for futu in self._futures:
            futu.cancel()


    def data_received(self, data: bytes):
        if self._stage == 0:
            self._stage = 1
            self._handle_authorised(data)
        elif self._stage == 1:
            self._stage = 2
            self._handle_connect(data)
        elif self._stage == 2:
            self._handle_stream(data)
        else:
            log.error("stage error")


    def _handle_authorised(self, data: bytes):
        self._transport.write(b"\x05\x00")

    def _handle_connect(self, data: bytes):
        atype = data[3]
        addr = data[4:-2]
        port = data[-2:]
        self._con_data = data
        if atype == self.ATYPE_IPV4 or atype == self.ATYPE_IPV6:
            host = addr.decode("ascii")
        elif atype == self.ATYPE_DOMN:
            host = addr[1:].decode("utf-8")
        else:
            log.error("no such atype: %d", atype)
            return

        port = self._port_b2i(port)
        log.info("%s:%d", host, port)
        coro = self._loop.getaddrinfo(host, port)
        futu = asyncio.ensure_future(coro)
        futu.add_done_callback(self._future_get_addrinfo)
        self._futures.append(futu)


    def _handle_stream(self, data: bytes):
        try:
            self._socket.sendall(data)
        except BrokenPipeError:
            log.error("BrokenPipeError")
            self._transport.write(b"\x05\x01" + self._con_data[2:])


    def _future_get_addrinfo(self, futu):
        try:
            info = futu.result()
        except asyncio.CancelledError:
            log.warning("future canceled")
            return
        info = info[0]
        self._socket = socket.socket(info[0], info[1], info[2])
        self._socket.setblocking(False)
        coro = self._loop.sock_connect(self._socket, info[-1])
        futu2 = asyncio.ensure_future(coro)
        futu2.add_done_callback(self._future_sock_connect)
        self._futures.append(futu2)

    def _future_sock_connect(self, futu):
        if self._socket.fileno() == -1:
            log.warning("error socket")
            self._transport.write(b"\x05\x01" + self._con_data[2:])
            return

        try:
            log.info("%s connected", self._socket.getpeername())
        except OSError:
            log.error("connect error")
            self._transport.write(b"\x05\x01" + self._con_data[2:])
            return

        self._loop.add_reader(self._socket, self._recv)
        self._transport.write(b"\x05\x00" + self._con_data[2:])

    def _recv(self):
        data = self._socket.recv(512)
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
    # loop.set_debug(True)
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