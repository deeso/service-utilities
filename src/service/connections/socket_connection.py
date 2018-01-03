from .base_connection import ConnectionFactory
import socket


class TCPConnection(ConnectionFactory):
    KEY = "TCPConnection"
    URI_TYPE = 'tcp'

    def __init__(self, uri, ip_type='ipv4', meta={}, **kargs):
        host = uri.split('tcp://')[1].split(':')[0]
        port = int(uri.split('tcp://')[1].split(':')[0])
        ConnectionFactory.__init__(self, uri=uri, host=host,
                                   port=port, **kargs)
        self.meta = meta

    def get_socket(self):
        if self._socket is None and self.ip_type == 'ipv6':
            self._socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            self._socket.connect()
        elif self._socket is None:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect()
        return self._socket

    def send(self, data):
        _data = data
        sent = 0
        remaining = len(data)
        if self.socket is None:
            raise Exception("Invalid Socket")

        while remaining > 0:
            sent = self.socket.send(_data)
            remaining += -sent
            _data = _data[sent:]
            if sent == 0:
                break

        return len(data) - remaining


class UDPConnection(ConnectionFactory):
    KEY = "UDPConnection"
    URI_TYPE = 'udp'

    def __init__(self, uri, meta={}, ip_type='ipv4', **kargs):
        host = uri.split('tcp://')[1].split(':')[0]
        port = int(uri.split('tcp://')[1].split(':')[0])
        ConnectionFactory.__init__(self, uri=uri, host=host,
                                   port=port, **kargs)
        self.meta = meta

    def get_socket(self):
        if self._socket is None and self.ip_type == 'ipv6':
            self._socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        elif self._socket is None:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return self._socket

    def sendto(self, data, addr=None, host=None, port=None):
        _data = data
        sent = 0
        remaining = len(data)
        if self.socket is None:
            raise Exception("Invalid Socket")

        if (host is None and port is None) and addr is None:
            raise Exception("Missing destination")
        elif (host is not None and port is not None):
            addr = (host, port)
        elif (not isinstance(addr, tuple) and
              isinstance(addr, tuple)) or len(addr) != 2:
            addr = (host, port)

        while remaining > 0:
            sent = self.socket.sendto(_data, addr)
            remaining += -sent
            _data = _data[sent:]
            if sent == 0:
                break

        return len(data) - remaining
