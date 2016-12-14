# encoding=utf8
import jenkins_job_wrecker.modules.base


class Buildwrappers(jenkins_job_wrecker.modules.base.Base):
    component = 'buildwrappers'

    def gen_yml(self, yml_parent, data):
        wrappers = []
        for child in data:
            object_name = child.tag.split('.')[-1].lower()
            self.registry.dispatch(self.component, object_name, child, wrappers)
        yml_parent.append(['wrappers', wrappers])


def envinjectpasswordwrapper(top, parent):
    inject = {}
    for element in top:
        if element.tag == 'injectGlobalPasswords':
            inject['global'] = (element.text == 'true')
        elif element.tag == 'maskPasswordParameters':
            inject['mask-password-params'] = (element.text == 'true')
        elif element.tag == 'passwordEntries':
            if len(list(element)) > 0:
                raise NotImplementedError('TODO: implement handling '
                                          'here')
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % element.tag)
    parent.append({'inject': inject})


def envinjectbuildwrapper(top, parent):
    build_inject = {}
    for element in top:
        if element.tag == 'info':
            for subelement in element:
                if subelement.tag == 'propertiesFilePath':
                    build_inject['properties-file'] = subelement.text
                if subelement.tag == 'loadFilesFromMaster':
                    pass
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % element.tag)
    parent.append({'inject': build_inject})


def buildtimeoutwrapper(top, parent):
    pass


def ansicolorbuildwrapper(top, parent):
    parent.append({'ansicolor': {'colormap': 'xterm'}})


def sshagentbuildwrapper(top, parent):
    ssh_agents = {}
    for element in top:
        if element.tag == 'credentialIds':
            keys = []
            for key in element:
                keys.append(key.text)
            ssh_agents['users'] = keys
        elif element.tag == 'ignoreMissing':
            pass
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % element.tag)
    parent.append({'ssh-agent-credentials': ssh_agents})


def buildnamesetter(top, parent):
    parent.append({'build-name': {'name': top[0].text}})


def timestamperbuildwrapper(top, parent):
    parent.append('timestamps')


def prebuildcleanup(top, parent):
    preclean = {}
    preclean_patterns = {'include': '', 'exclude': ''}
    for element in top:
        if element.tag == 'deleteDirs':
            preclean['dirmatch'] = (element.text == 'true')
        elif element.tag == 'patterns':
            for subelement in element:
                if subelement.tag != 'hudson.plugins.ws__cleanup.Pattern':
                    raise NotImplementedError("cannot handle "
                                              "XML %s" % subelement.tag)
                if subelement.find('type') is not None and subelement.find('pattern') is not None:
                    rule_type = subelement.find('type').text.lower()
                    rule_patt = subelement.find('pattern').text
                    preclean_patterns[rule_type] = rule_patt
        elif element.tag == 'cleanupParameter':
            # JJB does not seem to support this. Ignored.
            pass
        elif element.tag == 'externalDelete':
            # JJB does not seem to support this. Ignored.
            pass
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % subelement.tag)

    for rule in preclean_patterns:
        if preclean_patterns[rule] is not None and len(preclean_patterns[rule]) > 0:
            preclean[rule] = preclean_patterns[rule]

    if len(preclean) > 0:
        parent.append({'workspace-cleanup': preclean})
    else:
        parent.append('workspace-cleanup')


def xvfbbuildwrapper(top, parent):
    xvfb = {}
    for element in top:
        if element.tag == 'installationName':
            xvfb['installation-name'] = element.text
        if element.tag == 'autoDisplayName':
            xvfb['auto-display-name'] = (element.text == 'true')
        if element.tag == 'displayName':
            xvfb['display-name'] = element.text
        if element.tag == 'assignedLabels':
            xvfb['assigned-labels'] = element.text
        if element.tag == 'parallelBuild':
            xvfb['parallel-build'] = (element.text == 'true')
        if element.tag == 'timeout':
            xvfb['timeout'] = element.text
        if element.tag == 'screen':
            xvfb['screen'] = element.text
        if element.tag == 'displayNameOffset':
            xvfb['display-name-offset'] = element.text
        if element.tag == 'additionalOptions':
            xvfb['additional-options'] = element.text
        if element.tag == 'debug':
            xvfb['debug'] = (element.text == 'true')
        if element.tag == 'shutdownWithBuild':
            xvfb['shutdown-with-build'] = (element.text == 'true')

    parent.append({'xvfb': xvfb})


def maskpasswordsbuildwrapper(top, parent):
    parent.append('mask-passwords')
