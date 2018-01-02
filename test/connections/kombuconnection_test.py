# import docker
from service.utilities.connection import ConnectionFactory, KombuConnection
import unittest
from unittest import TestCase
import toml

EXAMPLE_TOML = '''
uri = 'redis://0.0.0.0:6379'
queue_name = "testing_msgs"
name = "testing"
'''


class TestKombuClientConnection(TestCase):

    def test_parseblock(self):
        config_dict = toml.loads(EXAMPLE_TOML)
        conn = ConnectionFactory.create_connection(**config_dict)
        self.assertTrue(isinstance(conn, KombuConnection))
        self.assertTrue(conn.name == 'testing')

    def test_send_recv_operation(self):
        config_dict = toml.loads(EXAMPLE_TOML)
        conn = ConnectionFactory.create_connection(**config_dict)
        self.assertTrue(isinstance(conn, KombuConnection))
        msg_data = {'testinging': 1234, 'lala': 'fafa'}
        conn.send_message(msg_data)
        # nsock = conn.socket
        msg = conn.recv_message()
        for k, v in list(msg.items()):
            self.assertTrue(k in msg_data)
            self.assertTrue(msg_data[k] == v)

        empty_queue = False
        try:
            msg = conn.recv_message()
            empty_queue = True
        except:
            pass

        self.assertTrue(empty_queue)

if __name__ == '__main__':
    unittest.main()
