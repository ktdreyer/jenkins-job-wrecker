# encoding=utf8
class Base(object):
    registry = None
    component = None

    def __init__(self, registry):
        self.registry = registry
        self.registry.register(self.component)

    def gen_xml(self, yml_parent, data):
        pass
