# encoding=utf8
from importlib import import_module
from inspect import getmembers, isfunction, isclass
from jenkins_job_wrecker.helpers import gen_raw
import jenkins_job_wrecker.modules
from os.path import dirname
from pkg_resources import iter_entry_points
from pkgutil import iter_modules


class DuplicateEntryPoint(Exception):
    pass


class Registry(object):
    registry = {}
    project_types = {}

    def __init__(self, ignore_actions=False):
        self.__handlers()
        self.ignore_actions = ignore_actions

    def _get_entry_points(self, name):
        found = {}
        for ep in iter_entry_points(group=name):
            if ep.name in found:
                msg = 'Entry point {0} already defined for {1}'.format(ep.name, name)
                raise DuplicateEntryPoint(msg)
            found[ep.name] = ep.load()
        return found

    def get_project_types(self):
        if len(self.project_types) == 0:
            valid_types = {'project': 'freestyle',
                           'matrix-project': 'matrix',
                           'com.cloudbees.plugins.flow.BuildFlow': 'flow',
                           'flow-definition': 'pipeline',
                           'com.cloudbees.hudson.plugins.folder.Folder': 'folder',
                           'hudson.model.ListView': 'listview'}
            for name, item in self._get_entry_points('jenkins_job_wrecker.projects').iteritems():
                valid_types.update(item)
            self.project_types.update(valid_types)
        return self.project_types

    def register(self, component):
        mod = import_module('jenkins_job_wrecker.modules.{0}'.format(component))
        if component not in self.registry:
            self.registry[component] = {}
        self.registry[component].update({name: obj
                                         for name, obj in getmembers(mod)
                                         if isfunction(obj)})
        entry_points = self._get_entry_points('jenkins_job_wrecker.{0}'.format(component))
        self.registry[component].update(entry_points)

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
        except (KeyError, NotImplementedError) as e:
            if self.ignore_actions and name == 'actions':
                print('WARNING: {0} Ignoring because of -a...'.format(e))
                return
            elif component == 'handlers':
                raise
            gen_raw(xml, parent)

    def __handlers(self):
        self.registry['handlers'] = {}
        pkgpath = dirname(jenkins_job_wrecker.modules.__file__)
        for name in [name
                     for _, name, _ in iter_modules([pkgpath])
                     if name not in ['handlers', 'base']]:
            my_mod = import_module('jenkins_job_wrecker.modules.%s' % name)
            my_obj = getattr(my_mod, name.capitalize())
            self.registry['handlers'].update({name: my_obj})
