# fake out handlers so the handle messages properly


class FauxMessage(object):
    KEY = "FauxMessage"

    def __init__(self, data=''):
        self.data = data

    @property
    def payload(self):
        return self._data

    def ack(self):
        return True

    @classmethod
    def key(cls):
        return cls.KEY.lower()
