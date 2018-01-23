LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 3128


class Proxy(object):
    HTTP_HOST = "http_host"
    HTTP_PORT = "http_port"

    HTTPS_HOST = "https_host"
    HTTPS_PORT = "https_port"

    DFLT_HTTP_PORT = 3128
    DFLT_HTTP_HOST = "127.0.0.1"
    DFLT_HTTPS_PORT = 3128
    DFLT_HTTPS_HOST = "127.0.0.1"
    HOST_FORMAT = "%s:%s"

    def __init__(self, http_host=LOCAL_HOST, http_port=LOCAL_PORT,
                 https_host=LOCAL_HOST, https_port=LOCAL_PORT):

        self.http_host = http_host
        self.http_port = http_port
        self.https_port = https_port
        self.https_port = https_port

    def get_http(self):
        if self.http_host is not None:
            return self.HOST_FORMAT % (self.http_host, self.http_port)
        return None

    def get_https(self):
        if self.https_host is not None:
            return self.HOST_FORMAT % (self.https_host, self.https_port)
        return None

    def get_proxies(self):
        http = self.get_http()
        https = self.get_https()
        r = {}
        if http is not None:
            r['http'] = http
        if https is not None:
            r['https'] = https
        return r

    @classmethod
    def parse_toml(cls, toml_dict):
        http_host = toml_dict.get(cls.HTTP_HOST, cls.DFLT_HTTP_HOST)
        http_port = toml_dict.get(cls.HTTP_PORT, cls.DFLT_HTTP_PORT)
        https_host = toml_dict.get(cls.HTTPS_HOST, cls.DFLT_HTTPS_HOST)
        https_port = toml_dict.get(cls.HTTPS_PORT, cls.DFLT_HTTPS_PORT)
        return cls(http_host=http_host, http_port=http_port,
                   https_host=https_host, https_port=https_port)
