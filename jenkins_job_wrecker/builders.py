# encoding=utf8
from inspect import getmembers, isfunction
from pkg_resources import iter_entry_points
from sys import modules


class BuilderRegister(object):
    def __init__(self):
        self.builders = {name: obj
                         for name,obj in getmembers(modules[__name__])
                         if isfunction(obj)}
        for ep in iter_entry_points(group='jenkins_job_wrecker.builders'):
            self.builders.update({ep.name: ep.load()})

    def __getitem__(self, name):
        try:
            return self.builders[name]
        except KeyError:
            # No valid handler
            raise NotImplementedError("cannot handle builder %s" % name)


def copyartifact(child, parent):
    copyartifact = {}
    selectdict = {
        'StatusBuildSelector': 'last-successful',
        'LastCompletedBuildSelector': 'last-completed',
        'SpecificBuildSelector': 'specific-build',
        'SavedBuildSelector': 'last-saved',
        'TriggeredBuildSelector': 'upstream-build',
        'PermalinkBuildSelector': 'permalink',
        'WorkspaceSelector': 'workspace-latest',
        'ParameterizedBuildSelector': 'build-param',
        'DownstreamBuildSelector': 'downstream-build'}
    for copy_element in child:
        if copy_element.tag == 'project':
            copyartifact[copy_element.tag] = copy_element.text
        elif copy_element.tag == 'filter':
            copyartifact[copy_element.tag] = copy_element.text
        elif copy_element.tag == 'target':
            copyartifact[copy_element.tag] = copy_element.text
        elif copy_element.tag == 'excludes':
            copyartifact['exclude-pattern'] = copy_element.text
        elif copy_element.tag == 'selector':
            select = copy_element.attrib['class']
            select = select.replace('hudson.plugins.copyartifact.', '')
            copyartifact['which-build'] = selectdict[select]
        elif copy_element.tag == 'flatten':
            copyartifact[copy_element.tag] = \
                (copy_element.text == 'true')
        elif copy_element.tag == 'doNotFingerprintArtifacts':
            # Not yet implemented in JJB
            # ADD RAW XML
            continue
        elif copy_element.tag == 'optional':
            copyartifact[copy_element.tag] = \
                (copy_element.text == 'true')
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % copy_element.tag)
    parent['copyartifact'] = copyartifact


def maven(child, parent):
    maven = {}
    for maven_element in child:
        if maven_element.tag == 'targets':
            maven['goals'] = maven_element.text
        elif maven_element.tag == 'mavenName':
            maven['name'] = maven_element.text
        elif maven_element.tag == 'usePrivateRepository':
            maven['private-repository'] = (maven_element.text == 'true')
        elif maven_element.tag == 'settings':
            maven['settings'] = maven_element.attrib['class']
        elif maven_element.tag == 'globalSettings':
            maven['global-settings'] = maven_element.attrib['class']
        else:
            continue
    parent['maven-target'] = maven


def shell(child, parent):
    shell = ''
    for shell_element in child:
        # Assumption: there's only one <command> in this
        # <hudson.tasks.Shell>
        if shell_element.tag == 'command':
            if shell_element.text is not None:
                shell = str(shell_element.text)
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % shell_element.tag)
        parent['shell'] = shell
