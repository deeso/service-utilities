from connection import ConnectionFactory
from hashlib import sha256


class FilterConnection(object):
    KEY = "FilterConnection"

    def __init__(self, **kargs):
        self.conn = None
        self.gen_id_from = kargs.get('gen_id_from', None)
        if self.gen_id_from is None:
            self.gen_id_from = lambda x: str(x)

        self.gen_id = kargs.get('gen_id', None)
        if self.gen_id is None:
            self.gen_id = lambda x: sha256(str(x).encode('utf-8')).hexdigest()

    def insert_unique(self, dict_object):
        raise Exception("Not implemented")

    def insert(self, dict_object):
        raise Exception("Not implemented")

    def get_obj(self, dict_object):
        raise Exception("Not implemented")

    def has_obj(self, dict_object):
        raise Exception("Not implemented")

    def is_unique_obj_found(self, dict_object):
        raise Exception("Not implemented")

    @classmethod
    def key(cls):
        return cls.KEY.lower()


class MongoFilterConnection(FilterConnection):
    KEY = "MongoFilterConnection"

    def __init__(self, dbname=None, colname=None, uri=None,
                 gen_id=None, gen_id_from=None, **kargs):
        super(FilterConnection, self).__init__(self, gen_id=None,
                                               gen_id_from=None, **kargs)

        self.conn = ConnectionFactory.create_connection(uri=uri,
                                                        dbname=dbname,
                                                        colname=colname)

    def insert(self, dict_object):
        return self.insert_msg(dict_object, unique=False)

    def has_obj(self, dict_object):
        items = self.find_by_id(dict_object)
        return len(items) > 0

    def is_unique_obj(self, dict_object):
        items = self.find_by_id(dict_object)
        return len(items) == 1

    def find_by_id(self, id_value=None, msg_value=None,
                   gen_id=None, gen_id_from=None):
        gid = self.gen_id if gen_id is None else gen_id
        gid_from = self.gen_id_from if gen_id_from is None else gen_id_from

        if msg_value is not None:
            content = gid_from(msg_value)
            id_value = gid(content)

        if id_value is None:
            return None
        return self.conn.find_by_id(id_value=id_value)

    def insert_unique(self, dict_object):
        return self.insert_msg(dict_object, unique=True)
