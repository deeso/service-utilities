class PythonNamedCode(object):

    def __init__(self, name: str, code: str):
        self.name = name
        self.code = code
        self.block_name = None
        self.co = None
        self.cls_obj = None

        # FIXME hack to deal with class and def statements
        tokens = code.strip().replace('(', ' ').split()
        if tokens[0] == 'class' or tokens[0] == 'def':
            self.block_name = tokens[1]
        elif code.find('=') > 0:
            identifier = code.split('=')[0].strip()
            is_lambda = code.split('=')[1].strip().split()[0] == 'lambda'
            if is_lambda:
                self.block_name = identifier

    @classmethod
    def parse(cls, config_dict: dict):
        name = config_dict.get('name', None)
        code = config_dict.get('code', None)

        if name is None or code is None:
            return None

        return cls(name=name, code=code)

    def compile(self):
        self.co = None
        self.cls_obj = None
        if self.block_name is None:
            raise Exception("Unable to determine the segment's identifier")

        try:
            self.co = compile(self.code, '<string>', 'exec')
        except Exception as e:
            raise Exception("Unable to load code for (%s): %s" %
                            (self.name, str(e)))

        if self.co is not None:
            exec(self.co)

        self.cls_obj = globals().get(self.block_name, None)
        if self.cls_obj is None:
            self.cls_obj = locals().get(self.block_name, None)

        if self.cls_obj is None:
            raise Exception("Unable to find page object(%s)" %
                            self.name)
        return self.cls_obj

    def get(self):
        if self.cls_obj is None:
            return self.compile()
        return self.cls_obj
