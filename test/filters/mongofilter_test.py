from spoton.util.pythonfn import PythonNamedCode
from unittest import TestCase
import json
from hashlib import sha256
import toml

EXAMPLE_TOML = """
[python_fns.gen_id]
name = 'gen_id'
code = '''def gen_id(str_val: str):
    import hashlib.sha256
    return hashlib.sha256(str_val.encode('utf-8')).hexdigest()
'''

[python_fns.gen_id_from]
name = 'gen_id_from'
code = '''def gen_id(json_msg: dict):
    return str(json_msg)
'''

[filters.mongo-memory]
name = 'mongo-memory'
uri = 'mongodb://127.0.0.1:6379'
dbname = 'mongo-memory'
colname = 'logstash'
gen_id_from = 'python_fns.gen_id_from'
gen_id = 'python_fns.gen_id'
"""

class TestMongoFilterTest(TestCase):

    def test_pythonfns(self):
        config_dict = toml.loads(EXAMPLE_TOML)
        # parse pythonfn
        pyfns = {}
        for d in list(config_dict.get('python_fns')):
            pyfn = PythonNamedCode.parse(d)
            pyfns[pyfn.name] = pyfn

        v = {'test': 1234}
        vjson = json.dumps(v)
        vhash = sha256(test).hexdigest()

        tjson = pyfn['gen_id_from'].get(v)
        self.assertTrue(tjson == vjson)





    def test_parseblock(self):
        filters = []
        conn = ConnectionFactory.create_connection(**config_dict)
        self.assertTrue(isinstance(conn, MongoConnection))
        self.assertTrue(conn.name == 'testing')
        self.assertTrue(conn.default_dbname == 'mydefault')
        self.assertTrue(conn.default_colname == 'mydefault_col')
        self.assertTrue(conn.id_key == 'msg2_id')



    def test_send_recv_operation(self):
        config_dict = toml.loads(EXAMPLE_TOML)
