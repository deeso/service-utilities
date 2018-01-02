# import docker
from service.utilities.connection import ConnectionFactory, MongoConnection
import unittest
from unittest import TestCase
import toml

EXAMPLE_TOML = '''

uri = 'mongodb://127.0.0.1:27017'
name = "testing"
default_dbname = 'mydefault'
default_colname = 'mydefault_col'
id_key = 'msg2_id'


'''


class TestMongoClientConnection(TestCase):

    def test_parseblock(self):
        config_dict = toml.loads(EXAMPLE_TOML)
        conn = ConnectionFactory.create_connection(**config_dict)
        self.assertTrue(isinstance(conn, MongoConnection))
        self.assertTrue(conn.name == 'testing')
        self.assertTrue(conn.default_dbname == 'mydefault')
        self.assertTrue(conn.default_colname == 'mydefault_col')
        self.assertTrue(conn.id_key == 'msg2_id')

    def test_insert_unique(self):
        id_value = 'unique'
        x = {'test': 1234, 'msg2_id': id_value}
        config_dict = toml.loads(EXAMPLE_TOML)
        mongoconn = ConnectionFactory.create_connection(**config_dict)
        mongoconn.get_collection().drop()
        inserted, oid = mongoconn.insert_msg(x, unique=True)
        try:
            inserted, oid2 = mongoconn.insert_msg(x, unique=True)
            self.assertTrue(oid == oid2)
            self.assertFalse(inserted)
        except:
            raise

        col_conn = mongoconn.get_collection()

        items = [i for i in col_conn.find({'_id': id_value}).limit(3)]
        self.assertTrue(len(items) == 1)
        self.assertTrue('test' in items[0] and items[0]['_id'] == 'unique')
        mongoconn.get_collection().drop()

    def test_insert_nonunique(self):
        id_value = 'non-unique'
        x = {'test': 1234, 'msg2_id': id_value}
        y = {'test': 1234}
        z = {'test': 12345}
        config_dict = toml.loads(EXAMPLE_TOML)
        mongoconn = ConnectionFactory.create_connection(**config_dict)
        mongoconn.get_collection().drop()
        inserted, oid = mongoconn.insert_msg(x, unique=False)
        try:
            inserted, oid2 = mongoconn.insert_msg(y, unique=False)
            self.assertTrue(oid != oid2)
            self.assertTrue(inserted)
            inserted, oid23 = mongoconn.insert_msg(z, unique=False)
            self.assertTrue(oid23 != oid2)
            self.assertTrue(inserted)
        except:
            raise

        col_conn = mongoconn.get_collection()

        items = [i for i in col_conn.find().limit(3)]
        self.assertTrue(len(items) > 0)
        self.assertTrue(all(['test' in i and i['test'] >= 1234
                             for i in items]))
        mongoconn.get_collection().drop()

    # TODO publishers

    # TODO subscribers

if __name__ == '__main__':
    unittest.main()
