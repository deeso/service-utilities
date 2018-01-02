import toml
import os
from .connection import ConnectionFactory


class Parser(object):
    @classmethod
    def load_toml(cls, filename):
        try:
            os.stat(filename)
        except:
            raise Exception("Filename (%s) does not exist" % filename)

        try:
            return toml.load(open(filename, 'rb'))
        except:
            raise

    @classmethod
    def parse_connection(cls, config_dict):
        uri = config_dict.get('uri', None)
        kargs = {}
        kargs['name'] = config_dict.get('name', None)
        kargs['queue'] = config_dict.get('queue', None)
        kargs['meta'] = {}
        for k, v in list(config_dict.items()):
            if k in kargs:
                continue
            kargs['meta'][k] = v

        if uri is None:
            raise Exception("Connection missing URI")
        return ConnectionFactory.create_connection(uri, **kargs)

