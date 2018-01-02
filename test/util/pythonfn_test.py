from unittest import TestCase
from spoton.util.pythonfn import PythonNamedCode
import json
import toml
from hashlib import sha256

EXAMPLE_TOML = """
[python_fns.gen_id]
name = 'gen_id'
code = '''def gen_id(str_val: str):
    from hashlib import sha256
    return sha256(str_val.encode('utf-8')).hexdigest()
'''

[python_fns.gen_id_from]
name = 'gen_id_from'
code = '''def gen_id(json_msg: dict):
    import json
    return json.dumps(json_msg)
'''
"""


class TestNamedPythonFn(TestCase):

    def test_attemptlambda(self):
        name = 'ltest'
        code = 'lambda x: x'
        pfn = PythonNamedCode(name, code)
        try:
            pfn.compile()
            # compiling pure lambdas not allowed
            self.assertTrue(False)
        except:
            self.assertTrue(True)

    def test_assignedlambda(self):
        name = 'ltest'
        code = 'petri = lambda x: x'
        pfn = PythonNamedCode(name, code)
        try:
            co = pfn.compile()
            v = "test"
            v_ = co(v)
            self.assertTrue(v == v_)
        except:
            self.assertTrue(False)

    def test_code(self):
        name = 'ctest'
        code = 'def test(x):\n\treturn x'
        pfn = PythonNamedCode(name, code)
        try:
            co = pfn.compile()
            v = "test"
            v_ = co(v)
            self.assertTrue(v == v_)
        except:
            self.assertTrue(False)

    def test_pythonfns(self):
        config_dict = toml.loads(EXAMPLE_TOML)
        # parse pythonfn
        pyfns = {}
        for d in list(config_dict.get('python_fns').values()):
            pyfn = PythonNamedCode.parse(d)
            pyfns[pyfn.name] = pyfn

        v = {'test': 1234}
        vjson = json.dumps(v)
        vhash = sha256(vjson.encode('utf-8')).hexdigest()

        tjson = pyfns['gen_id_from'].get()(v)
        self.assertTrue(tjson == vjson)

        thash = pyfns['gen_id'].get()(tjson)
        self.assertTrue(thash == vhash)
