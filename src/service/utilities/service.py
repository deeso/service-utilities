import threading
from service.utilities.page import AddPage, DefaultServiceApp
from spoton.util.pythonfn import PythonNamedCode

# FIXME SSL stuff is broken
# from cheroot.wsgi import Server as CherryPyWSGIServer
# from web.wsgiserver.ssl_builtin import BuiltinSSLAdapter


class Service(object):
    KEY = "Service"

    def __init__(self, frontend=None, port=1080, host='0.0.0.0', pages=[],
                 logger=None, ssl_cert_path=None, ssl_key_path=None,
                 app_debug=False):

        self.app_debug = app_debug
        self.logger = logger
        if frontend is None:
            raise Exception("frontend is required")

        self.frontend = frontend
        self.pages = pages
        self._app = None
        self.app_thread = None
        self.port = port
        self.host = host
        self._keep_running = False

        self.handlers = {}
        for page in pages:
            self.handlers[page.NAME] = page.handle_service_request

        print (self.handlers)
        if not self.has_page(name='add_page'):
            self.pages.append(AddPage)

        # if ssl_cert_path is not None and ssl_key_path is not None:
        #     ssl_adapter = BuiltinSSLAdapter(ssl_cert_path, ssl_key_path, None)
        #     CherryPyWSGIServer.ssl_adapter = ssl_adapter
    def has_page(self, page=None, name=None):
        if name is not None and name not in set([i.name for i in self.pages]):
            return True
        elif page is not None and \
             page.name not in set([i.name for i in self.pages]):
            return True
        return False

    # @property
    # def app(self):
    #     if self._app is None:
    #         self._app = DefaultServiceApp(self.urls,
    #                                       globals())
    #     return self._app

    # @property
    # def app_thread(self):
    #     if self._app_thread is None or not self._app_thread.isAlive():
    #         kargs = {
    #                 'host': self.host,
    #                 'port': self.port,
    #                 'frontend': self.frontend
    #                 }
    #         self._app_thread = threading.Thread(target=self.app.run,
    #                                             kwargs=kargs)
    #     return self._app_thread

    def info(self, msg):
        if self.logger is not None:
            self.logger.info(msg)

    def error(self, msg):
        if self.logger is not None:
            self.logger.error(msg)

    def debug(self, msg):
        if self.logger is not None:
            self.logger.debug(msg)

    def start_service(self):
        if self.is_running():
            return self.is_running()
        self.info("Starting mgmt service: %s:%d" % (self.host, self.port))
        kargs = {
                'host': self.host,
                'port': self.port,
                'frontend': self.frontend
                }
        self.app = DefaultServiceApp(self.key()+'_svc',
                                     frontend=self.frontend,
                                     port=self.port,
                                     host=self.host,
                                     pages=self.pages)

        kargs = {'debug': self.app_debug}
        self.app_thread = threading.Thread(target=self.app.run, kwargs=kargs)
        self.app_thread.start()
        return self.app_thread.isAlive()

    def stop_service(self):
        self.info("Stopping mgmt service: %s:%d" % (self.host, self.port))
        self.app.stop()
        self.app_thread.join()
        self._app_thread = None
        self._app = None

    def is_running(self):
        return self.app_thread is not None and self.app_thread.isAlive()

    def add_page(self, page_name, page_code):
        # self.stop_service()
        if self.app.has_page(page_name):
            return {'msg': 'already exists'}
        pfn = PythonNamedCode(page_name, page_code)
        page_cls = pfn.compile()
        return self.add_page(page_name, page_cls)

    def add_page_obj(self, page_name, page_cls):
        if self.app.has_page(page_name):
            return {'msg': 'already exists'}

        # if self.is_running():
        #     self.stop_service()

        if page_cls is None:
            self.error("Page class (%s) failed to compile" % page_name)
            return {'msg': "Page class (%s) failed to compile" % page_name}

        handler_fn = getattr(page_cls, 'handle_service_request', None)

        if page_cls is None or handler_fn is None:
            # self.start_service()
            self.info("Failed to add the new page")
            return {'msg': "Failed to add the new page"}

        self.app.add_page(page=page_cls)
        if not self.has_page(name=page_name):
            self.pages.append(page_cls)

        # for uri in page_uris:
        #     self.pages.append(uri)
        #     self.pages.append(page_name)

        self.handlers[page_name] = handler_fn
        # self.start_service()

        return {'msg': 'success'}

    def handle_request(self, data=None,
                       request=None):
        if data is None or request is None:
            return {'error': 'unable to process request'}

        page_name = request.path
        if page_name not in self.handlers:
            return {'error': 'page handler does not exist'}

        handler_fn = self.handlers[page_name]
        return handler_fn(service=self, frontend=self.frontend,
                          data=data, request=request)

    @classmethod
    def key(cls):
        return cls.KEY.lower()
