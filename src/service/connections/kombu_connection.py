from base_connection import ConnectionFactory
from kombu import Connection as _KombuConnection
import queue


class KombuConnection(ConnectionFactory):
    DEFAULT_QUEUE = 'default'
    KEY = "KombuConnection"

    def __init__(self, uri, queue=DEFAULT_QUEUE, meta={}, **kargs):
        v = uri
        host = None
        port = 6379 if uri.find('redis') == 0 else 5672
        if uri.find('@') > 0:
            v = uri.split('@')[1]
            if v.find(':') > 0:
                host = v.split(':')[0]
                ps = v.split(':')[1]
                if ps.find(',') > 0:
                    port = int(ps.split('/')[0])
                elif v.find('/') > 0:
                    port = int(ps.split('/')[0])
            elif v.find(',') > 0:
                host = v.split(',')[0]
            elif v.find('/') > 0:
                host = v.split('/')[0]
            else:
                host = v
        else:
            v = uri.split('://')[1]
            if v.find('://') > 0:
                host = v.split(':')[0]
                ps = v.split(':')[1]
                if ps.find(',') > 0:
                    port = int(ps.split('/')[0])
                elif v.find('/') > 0:
                    port = int(ps.split('/')[0])
            elif v.find(',') > 0:
                host = v.split(',')[0]
            elif v.find('/') > 0:
                host = v.split('/')[0]
            else:
                host = v

        ConnectionFactory.__init__(self, uri=uri, host=host,
                                   port=port, **kargs)
        self.meta = meta
        self._queue = None

    def get_socket(self):
        if self._socket is None:
            self._socket = _KombuConnection(self.uri, block=False)
        return self._socket

    @property
    def connection(self):
        return self.socket

    @property
    def queue(self):
        return self.simple_queue

    @property
    def simple_queue(self):
        if self._queue is None:
            self._queue = self.socket.SimpleQueue(self.queue_name)
        return self._queue

    def send_message(self, msg):
        try:
            self.simple_queue.put(msg)
            self.simple_queue.close()
        except:
            raise

    def recv_messages(self, cnt=100, callback=None, sz=8192):
        msgs = []
        read_all = False
        if cnt < 1:
            read_all = True

        while cnt > 0 or read_all:
            cnt += -1
            msg = self.recv_message(callback=callback)
            if msg is None:
                break
            msgs.append(msg)
        return msgs

    def recv_message(self, callback=None, sz=8192):
        data = None
        try:
            message = self.simple_queue.get(block=False)
            data = message.payload
            if callback is not None:
                callback(self, data)
            message.ack()
        except queue.Empty:
            pass
        return data

    def read_message(self, callback=None, sz=8192):
        return self.recv_message(callback=callback)
