import json
import struct

from service.utilities.message import FauxMessage

REGISTRY = {}


class ConnectionFactory(object):
    KEY = "ConnectionFactory"
    URI_TYPE = "NONE"

    @classmethod
    def uri_type(cls):
        return cls.URI_TYPE

    @classmethod
    def register_connection(cls, ccls):
        global REGISTRY
        REGISTRY[ccls.uri_type()] = ccls

    def __init__(self, name=None, host=None,
                 port=None, ip_type=None, **kargs):
        if uri is None:
            raise Exception("An URI must be specified")

        self._socket = None
        self._host = host
        self._port = host
        self._ip_type = ip_type
        self.name = name
        self.uri = uri
        for k, v in list(kargs.items()):
            setattr(self, k, v)

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def socket(self):
        return self.get_socket()

    def get_socket(self):
        raise Exception("Not implemented")

    def read_data(self, sz):
        raise Exception("Not implemented")

    def recv_messages(self, cnt=100, callback=None, sz=8192):
        msgs = []
        while cnt > 0:
            cnt += -1
            msg = self.recv_message(callback=callback, sz=sz)
            if msg is None:
                break
            msgs.append(msg)
        return msgs

    def recv_message(self, callback=None, sz=8192):
        data = self.recv_data(sz)
        if callback is not None:
            callback(data)
        msg = FauxMessage(data=data)
        if callback is not None:
            callback(msg)
        return msg

    def read_message(self, callback=None, sz=8192):
        return self.recv_message(callback=callback, sz=sz)

    def read_messages(self, cnt=100, callback=None, sz=8192):
        return self.recv_messages(cnt=cnt, callback=callback, sz=sz)

    def send(self, data):
        raise Exception("Not implemented")

    def sendto(self, data, addr):
        raise Exception("Not implemented")

    def send_message_dict(self, msg_dict):
        if hasattr(msg_dict, 'toJSON'):
            return self.send(msg_dict.toJSON())
        elif isinstance(msg_dict, dict):
            return self.send(json.dumps(msg_dict))

        raise Exception("Not implemented")

    def sendto_message_dict(self, msg_dict, addr):
        if hasattr(msg_dict, 'toJSON'):
            return self.sendto(msg_dict.toJSON())
        elif isinstance(msg_dict, dict):
            return self.sendto(json.dumps(msg_dict))

        raise Exception("Not implemented")

    def send_json_line(self, msg):
        data = None
        try:
            data = json.dumps(msg) + '\n'
        except:
            raise
        return self.send_message(self, data)

    def sendto_json_line(self, msg):
        data = None
        try:
            data = json.dumps(msg) + '\n'
        except:
            raise
        return self.send_message(self, data)

    def sendto_serialized(self, msg, addr, endian="<", sz_size=8):
        data = None
        try:
            data = msg.serialize()
            sz = None
            if sz_size == 8:
                sz = struct.pack(endian+"Q", data)
            elif sz_size == 4:
                sz = struct.pack(endian+"I", len(data) % 0xFFFFFFFF)
            elif sz_size == 2:
                sz = struct.pack(endian+"H", len(data) % 0xFFFF)
            else:
                sz = chr(len(data) % 255)

            data = sz + data
        except:
            raise
        return self.sendto(self, data, addr)

    def send_serialized(self, msg, endian="<", sz_size=8):
        data = None
        try:
            data = msg.serialize()
            sz = None
            if sz_size == 8:
                sz = struct.pack(endian+"Q", data)
            elif sz_size == 4:
                sz = struct.pack(endian+"I", len(data) % 0xFFFFFFFF)
            elif sz_size == 2:
                sz = struct.pack(endian+"H", len(data) % 0xFFFF)
            else:
                sz = chr(len(data) % 255)

            data = sz + data
        except:
            raise
        return self.send_message(self, data)

    def recv_serialized(self, sz_size=8, endian='<'):
        data = self.read_data(sz_size)
        sz = None
        if sz_size == 8:
            sz, _ = struct.unpack(endian+"Q", data)
        if sz_size == 4:
            sz, _ = struct.unpack(endian+"I", data)
        if sz_size == 2:
            sz, _ = struct.unpack(endian+"H", data)
        if sz_size == 1:
            sz = ord(data)
        try:
            return self.read_data(sz)
        except:
            raise

    @classmethod
    def create_connection(cls, uri, name=None, **kargs):
        global REGISTRY
        important_part = uri.strip().split('://')

        ccls = REGISTRY.get(important_part, None)
        if ccls is None:
            raise Exception("Unable to handle URI type: %s" % uri)

        return ccls(uri.strip(), name=name, **kargs)

    @classmethod
    def create_pubs_subs(cls, pub_subs_configs):
        pub_subs = {}
        for name, block in list(pub_subs_configs.items()):
            subscribers = {}
            publisher = block.get('publisher')
            uri = publisher.get('uri', None)
            p_vs = list(publisher.items())
            kargs = dict([(k, v) for k, v in p_vs if k != 'uri'])
            if uri is None:
                raise Exception('Invalid publisher configuration block')
            kargs['subscribers'] = subscribers
            for sname, sub in block.get('subscribers', {}):
                sub_uri = sub.get('uri', None)
                if sub_uri is None:
                    raise Exception('Invalid publisher configuration block')
                    ps_vs = list(sub.items())
                sub_kargs = dict([(k, v) for k, v in ps_vs if k != 'uri'])
                sub_con = cls.create_connection(sub_uri, **sub_kargs)
                subscribers[sname] = sub_con
            conn = cls.create_connection(uri, **kargs)
            pub_subs[name] = conn
        return pub_subs

    @classmethod
    def key(cls):
        return cls.KEY.lower()

    @classmethod
    def from_uri(cls, uri, **kargs):
        global REGISTRY
        for k, con_cls in REGISTRY.items():
            if con_cls.can_handle(uri):
                return con_cls.create_from_uri(uri, **kargs)
        return None

    @classmethod
    def can_handle(cls, uri):
        return uri.lower().find(cls.URI_TYPE) == 0

    @classmethod
    def create_from_uri(cls, uri, **kargs):
        return cls(uri, **kargs)
