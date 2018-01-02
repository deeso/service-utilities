ZP_TOML = """[pages.Test]
page_code = '''class TestPage(BasePage):
    NAME = 'add_page'
    PATTERN = '/' + NAME
    CLASS_NAME = "AddPage"

    @classmethod
    def handle_service_request(cls, service=None, frontend=None,
                               data=None, ctx=None, web=None, **kwargs):
        return {'msg': 'this is a test'}
'''


[python_fns]
gen_id = '''def gen_id(str_val):
    import hashlib.sha256
    return hashlib.sha256(str_val).hexdigest()
'''

gen_id_from = '''def gen_id(json_msg):
    return str(json_msg)
'''

[publishers.logstash-results]
type = 'kombuconnection'
name = 'logstash-results'
uri = 'redis://127.0.0.1:6379'
queuname = 'logstash-results'

[filters.mongo-memory]
type = 'mongoconnection'
name = 'mongo-memory'
uri = 'mongodb://127.0.0.1:6379'
dbname = 'mongo-memory'
colname = 'logstash'
gen_id_from = 'python_fns.gen_id_from'
gen_id = 'python_fns.gen_id'

[subscribers.logstash]
type = 'udpconnection'
sendtype = 'json-newline'
uri = 'udp://127.0.0.1:5002'

[backends.basic]
host = '0.0.0.0'
port = 10001
pages = ['status']




[service.zippy-plop-00]
type = "zippy-plop"
name = "zippy-plop-00"
msg_limit = 100
publishers = ['logstash-results',]
filters = ['mongo-memory',]
"""