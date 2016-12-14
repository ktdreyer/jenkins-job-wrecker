# encoding=utf8
from helpers import gen_raw
from importlib import import_module
from inspect import getmembers, isfunction, isclass
from jenkins_job_wrecker.helpers import gen_raw
import jenkins_job_wrecker.modules
from os.path import dirname
from pkg_resources import iter_entry_points
from pkgutil import iter_modules


class Registry(object):
    registry = {}

    def __init__(self):
        self.__handlers()

    def register(self, component):
        mod = import_module('jenkins_job_wrecker.modules.{0}'.format(component))
        if component not in self.registry:
            self.registry[component] = {}
        self.registry[component].update({name: obj
                                         for name, obj in getmembers(mod)
                                         if isfunction(obj)})
        for ep in iter_entry_points(group='jenkins_job_wrecker.{0}'.format(component)):
            self.registry[component].update({ep.name: ep.load()})

    def dispatch(self, component, name, xml, parent):
        try:
            my_obj = self.registry[component][name]
            if isfunction(my_obj):
                self.registry[component][name](xml, parent)
                return
            if isclass(my_obj):
                handler = my_obj(self)
                handler.gen_yml(parent, xml)
                return
        except (KeyError, NotImplementedError):
            if component == 'handlers':
                raise
            gen_raw(xml, parent)

    def __handlers(self):
        self.registry['handlers'] = {}
        pkgpath = dirname(jenkins_job_wrecker.modules.__file__)
        for name in [name
                     for  _, name, _ in iter_modules([pkgpath])
                     if name not in ['handlers', 'base']]:
            my_mod = import_module('jenkins_job_wrecker.modules.%s' % name)
            my_obj = getattr(my_mod, name.capitalize())
            self.registry['handlers'].update({name: my_obj})
