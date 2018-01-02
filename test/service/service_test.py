from unittest import TestCase
from service.utilities.service import Service
from service.utilities.page import BasePage
import json
import requests
import toml
import time

EXAMPLE_TOML = """
port = 7979
host = "0.0.0.0"
pages = []
"""

REQ = {'test': 1234}

class TestPage(BasePage):
    NAME = 'test_page'
    PATTERNS = ['/' + NAME, ]
    CLASS_NAME = 'TestPage'
    HANDLER = None

    @classmethod
    def handle_request(cls, **kargs):
        r = None
        if cls.HANDLER is None:
            r = {'error': 'service handler not set'}
        else:
            r = cls.HANDLER.handle_request(**kargs)
        return json.dumps(r)

    def handle_service_request(cls, service=None, frontend=None,
                               data=None, request=None):
        r = {'error': 'service handler not set'}
        if frontend is not None and hasattr(frontend, 'handle_test'):
            r = frontend.handle_test(service=service,
                                     data=data,
                                     request=request)
        return json.dumps(r)


class MockFrontEnd(object):
    def handle_test(self, service=None, data=None, request=None):
        test = 5678
        if data is None or not isinstance(data, dict):
            test = data.get('test', test)
        return {'error': '', 'msg': 'ftw!', 'test': test}


class TestService(TestCase):

    def testParse(self):
        config_dict = toml.loads(EXAMPLE_TOML)
        frontend = MockFrontEnd()

        svc = Service(frontend=frontend, **config_dict)
        svc.start_service()
        time.sleep(3.0)
        svc.stop_service()
        time.sleep(1.0)
        self.assertFalse(svc.is_running())

    def testTestPage(self):
        config_dict = toml.loads(EXAMPLE_TOML)
        config_dict['pages'] = [TestPage, ]
        frontend = MockFrontEnd()
        svc = Service(frontend=frontend, **config_dict)

        started = svc.start_service()
        self.assertTrue(started)
        self.assertTrue(svc.is_running())

        time.sleep(4.0)
        url = "http://{0}:{1}/{2}".format(svc.host, svc.port, TestPage.NAME)
        r = requests.post(url, json=REQ)
        print (r)
        print (r.text)
        self.assertTrue(r.status_code == 200)
        jd = r.json()
        self.assertTrue('test' in jd and jd['test'] == REQ['test'])
        self.assertTrue('msg' in jd and jd['msg'] == "ftw!")
        svc.stop_service()
        self.assertFalse(svc.is_running())


if __name__ == '__main__':
    unittest.main()
