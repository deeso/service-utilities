import requests
import json
from flask import Flask, jsonify, Response
from flask.views import MethodView
from flask import request


class DefaultServiceApp(object):
    KEY = "DefaultServiceApp"

    def __init__(self, name, frontend=None, port=1080,
                 host='0.0.0.0', pages=[]):
        self.app = Flask(name)
        self.pages = pages
        self.host = host
        self.port = port
        self.frontend = frontend

        self.add_page(ShutdownPage)

    def add_page(self, page):
        if not self.has_page(page=page):
            self.pages.append(page)
            page.update_app(self.app)

    def run(self, debug=False):
        return self.app.run(port=self.port, host=self.host, debug=debug)

    def has_page(self, page=None, name=None):
        if name is not None:
            return name in set([i.name for i in self.pages])
        elif page is not None:
            return page.name in set([i.name for i in self.pages])
        return False

    @classmethod
    def key(cls):
        return cls.KEY.lower()

    def stop(self):
        url = "http://{0}:{1}/{2}".format(self.host,
                                          self.port,
                                          ShutdownPage.name)
        r = requests.get(url)
        return r.json()


class BasePage(MethodView):
    PATTERNS = ['/', ]
    NAME = 'basepage'
    CLASS_NAME = 'BasePage'
    HANDLER = None

    @property
    def handler(cls):
        return cls.HANDLER

    @property
    def name(cls):
        return cls.NAME

    @classmethod
    def update_app(cls, app):
        for pattern in cls.PATTERNS:
            app.add_url_rule(pattern,
                             view_func=cls.as_view(cls.NAME))

    @classmethod
    def urls(cls):
        r = []
        for i in cls.PATTERNS:
            r.append(i)
            r.append(cls.CLASS_NAME)
        return r

    @classmethod
    def set_handler(cls, handler):
        cls.HANDLER = handler

    def handle_request(self, data):
        r = None
        if self.HANDLER is None:
            r = {'error': 'service handler not set'}
        else:
            r = self.handler.handle_request(data=data, request=request)
        js = json.dumps(r)
        return Response(js, status=200, mimetype='application/json')

    @classmethod
    def handle_service_request(cls, service=None, frontend=None,
                               data=None, request=None):
        r = {'error': 'service handler not does nothing'}
        return jsonify(r)

    def get(self):
        # TODO add authentication here
        data = request.get_json()
        return self.handle_request(data)

    def post(self):
        # TODO add authentication here
        data = request.get_json()
        return self.handle_request(data)


class AddPage(BasePage):
    NAME = 'add_page'
    PATTERN = '/' + NAME
    CLASS_NAME = "AddPage"

    @classmethod
    def handle_service_request(cls, service=None, frontend=None,
                               data=None, request=None):
        r = {'error': 'service or data is invalid'}
        if service is None or data is None:
            return r
        page_name = data.get('page_name', None)
        page_code = data.get('page_code', None)
        if page_name is None or page_code is None:
            r = {'error': 'data (e.g. page_code or page_code) is missing'}
            return r
        return service.add_page(page_name, page_code)

class ShutdownPage(BasePage):
    NAME = 'shutdown'
    PATTERN = '/' + NAME
    CLASS_NAME = "Shutdown"

    @classmethod
    def handle_service_request(cls, service=None, frontend=None,
                               data=None, request=None):
        r = {'error': 'service or data is invalid'}
        if service is None or data is None:
            return r
        page_name = data.get('page_name', None)
        page_code = data.get('page_code', None)
        if page_name is None or page_code is None:
            r = {'error': 'data (e.g. page_code or page_code) is missing'}
            return r
        return service.add_page(page_name, page_code)

    def shutdown_server(self):
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        r = {'msg': 'shutting down'}
        return r

    def get(self):
        # TODO add authentication here
        return self.shutdown_server()

    def post(self):
        # TODO add authentication here
        return self.shutdown_server()

