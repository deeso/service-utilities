import json
from .base_connection import ConnectionFactory
from .socket_connection import UDPConnection, TCPConnection


class JsonUDPLineConnection(UDPConnection):
    KEY = "JsonUDPConnection"
    URI_TYPE = 'udp-json-line'

    def __init__(self, uri, ip_type='ipv4', meta={}, **kargs):
        host = uri.split(self.URI_TYPE+'://')[1].split(':')[0]
        port = int(uri.split(self.URI_TYPE+'://')[1].split(':')[0])
        ConnectionFactory.__init__(self, uri=uri, host=host,
                                   port=port, **kargs)
        self.meta = meta

    def send_msg(self, data):
        try:
            d = json.dumps(data[:65507])
            return self.sendto(d)
        except:
            raise


class JsonTCPLineConnection(TCPConnection):
    KEY = "JsonTCPConnection"
    URI_TYPE = 'tcp-json-line'

    def __init__(self, uri, ip_type='ipv4', meta={}, **kargs):
        host = uri.split(self.URI_TYPE+'://')[1].split(':')[0]
        port = int(uri.split(self.URI_TYPE+'://')[1].split(':')[0])
        ConnectionFactory.__init__(self, uri=uri, host=host,
                                   port=port, **kargs)
        self.meta = meta

    def send(self, json_data):
        d = json_data[:65507]
        return self.sendto(d)
