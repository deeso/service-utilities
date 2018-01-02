from base_connection import ConnectionFactory
from pymongo import MongoClient
import logging
from hashlib import sha256


class MongoConnection(ConnectionFactory):
    DEFAULT_DB = 'default'
    DEFAULT_COLLECTION = 'default'
    DEFAULT_ID_KEY = 'msg_id'
    KEY = "MongoConnection"

    def __init__(self, uri, default_db=DEFAULT_DB, gen_id_from=lambda m: '',
                 gen_id=None, check_id=True,
                 default_collection=DEFAULT_COLLECTION, meta={}, **kargs):
        v = uri
        host = None
        port = 27017
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

        ConnectionFactory.__init__(self, uri=uri,
                                   host=host, port=port, **kargs)

        self.default_dbname = kargs.get('default_dbname', self.DEFAULT_DB)
        self.default_colname = kargs.get('default_colname',
                                         self.DEFAULT_COLLECTION)

        self.meta = meta
        self.id_key = kargs.get('id_key',
                                self.meta.get('id_key', self.DEFAULT_ID_KEY))
        self.gen_id_from = gen_id_from
        if gen_id is None:
            self.gen_id = lambda x: sha256(str(x).encode('utf-8')).hexdigest()
        else:
            self.gen_id = gen_id

        self.check_id = check_id
        self.logger = logging

    def get_collection(self, dbname=None, colname=None, msg=None):
        if msg is not None and dbname is not None:
            dbname = msg.get('mongo.%s.dbname' % self.name,
                             self.default_dbname)
        if msg is not None and colname is not None:
            colname = msg.get('mongo.%s.colname' % self.name,
                              self.default_colname)

        if dbname is None:
            dbname = self.default_dbname
        if colname is None:
            colname = self.default_colname

        return self.socket[dbname][colname]

    def insert_msg(self, msg, unique=False, gen_id=None, gen_id_from=None):
        id_key = msg.get('mongo.%s.id_key' % self.name, self.id_key)
        inserted, item_id = (False, None)
        if unique:
            gid = self.gen_id if gen_id is None else gen_id
            gid_from = self.gen_id_from if gen_id_from is None else gen_id_from
            id_key = msg.get('mongo.%s.id_key' % self.name, self.id_key)
            id_value = msg.get(id_key, None)
            inserted, item_id = self.insert_unique_msg(msg,
                                                       gen_id_from=gid_from,
                                                       gen_id=gid,
                                                       id_value=id_value)
        else:
            inserted, item_id = self.insert(msg)

        if not inserted and item_id is not None:
            m = "Failed to insert object (%s) because it exists" % item_id
            self.logger.debug(m)
        if inserted and item_id is not None:
            self.logger.debug("Inserted object (%s)" % item_id)
            # self.logger.debug(m)
        else:
            m = "Failed to insert object (%s) for unknown reason"
            self.logger.debug(m)
        return inserted, item_id

    def extract_dbname_from(self, msg_value):
        return msg_value.get('mongo.%s.dbname' %
                             self.name, self.default_dbname)

    def extract_colname_from(self, msg_value):
        return msg_value.get('mongo.%s.colname' %
                             self.name, self.default_colname)

    def insert_msg_callback(self, pub, msg):
        m = "Handling mongo insert (%s) for Publisher: %s" % \
            (self.name, pub.name)
        self.logger.debug(m)
        return self.insert_msg(msg)

    def find_by_id(self, id_value=None, msg_value=None,
                   gen_id=None, gen_id_from=None):
        gid = self.gen_id if gen_id is None else gen_id
        gid_from = self.gen_id_from if gen_id_from is None else gen_id_from

        if msg_value is not None:
            content = gid_from(msg_value)
            id_value = gid(content)

        if id_value is None:
            return None

        obj_dict = {'_id': id_value}
        items = self._get_objs(self.get_collection(msg=msg_value), obj_dict)
        if len(items) > 1:
            raise Exception("Found more than one item by the object ID")
        return items[0] if len(items) > 0 else None

    @classmethod
    def _get_objs(cls, col_conn, obj_dict):
        return [i for i in col_conn.find(obj_dict)]

    def get_objs(self, obj_dict):
        return self._get_objs(self.get_collection(msg=obj_dict), obj_dict)

    @classmethod
    def _has_obj(cls, col_conn, obj_dict):
        return len([i for i in col_conn.find(obj_dict).limit(1)]) > 0

    def has_obj(self, obj_dict):
        return self._has_obj(self.get_collection(msg=obj_dict), obj_dict)

    @classmethod
    def _insert(cls, col_conn, msg):
        if '_id' in msg:
            objs = cls._get_objs(col_conn, {'_id': msg.get('_id')})
            if len(objs) > 0:
                return False, msg.get('_id')
        inserted_obj = col_conn.insert_one(msg)
        return True, inserted_obj.inserted_id

    def insert(self, msg):
        return self._insert(self.get_collection(msg=msg), msg)

    @classmethod
    def _insert_unique_msg(cls, col_conn, msg, gid=None,
                           gid_from=None, id_value=None):

        failed_check = True
        if id_value is None and gid_from is not None and gid is None:
            content = gid_from(msg)
            id_value = sha256(str(content).encode('utf-8')).hexdigest()

        elif id_value is None and gid_from is not None:
            content = gid_from(msg)
            id_value = gid(content)

        if id_value is not None:
            failed_check = not cls._has_obj(col_conn, {'_id': id_value})
            if not failed_check:
                cur = col_conn.find({'_id': id_value}).limit(1)
                item = [i for i in cur][0]
                return False, item['_id']

        item = None
        item = {}
        item.update(msg)
        if id_value is not None:
            item['_id'] = id_value

        return True, col_conn.insert_one(item).inserted_id

    def insert_unique_msg(self, msg, gen_id_from=None,
                          gen_id=None, id_value=None):
        gid = self.gen_id if gen_id is None else gen_id
        gid_from = self.gen_id_from if gen_id_from is None else gen_id_from
        id_key = msg.get('mongo.%s.id_key' % self.name, self.id_key)
        id_value = msg.get(id_key, None)

        return self._insert_unique_msg(self.get_collection(msg=msg),
                                       msg, gid=gid, gid_from=gid_from,
                                       id_value=id_value)

    def get_socket(self):
        if self._socket is None:
            self._socket = MongoClient(self.uri)
        return self._socket

    def __getitem__(self, db_name):
        return self.socket[db_name]
