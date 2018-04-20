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
    FAIL = 'hudson.plugins.build__timeout.operations.FailOperation'
    DESC = 'hudson.plugins.build__timeout.operations.WriteDescriptionOperation'
    ABORT = 'hudson.plugins.build__timeout.operations.AbortOperation'
    ABSOLUTE = 'hudson.plugins.build_timeout.impl.AbsoluteTimeOutStrategy'
    DEADLINE = 'hudson.plugins.build_timeout.impl.DeadlineTimeOutStrategy'
    ELASTIC = 'hudson.plugins.build_timeout.impl.ElasticTimeOutStrategy'
    STUCK = 'hudson.plugins.build_timeout.impl.LikelyStuckTimeOutStrategy'
    ACTIVITY = 'hudson.plugins.build_timeout.impl.NoActivityTimeOutStrategy'

    timeout_inject = {}
    for element in top:
        if element.tag == 'strategy':
            if element.get('class') == ABSOLUTE:
                timeout_inject['type'] = 'absolute'
            elif element.get('class') == DEADLINE:
                timeout_inject['type'] = 'deadline'
            elif element.get('class') == ELASTIC:
                timeout_inject['type'] = 'elastic'
            elif element.get('class') == STUCK:
                timeout_inject['type'] = 'likely-stuck'
            elif element.get('class') == ACTIVITY:
                timeout_inject['type'] = 'no-activity'
            for subelement in element:
                if subelement.tag == 'timeoutMinutes':
                    timeout_inject['timeout'] = int(subelement.text)
                elif subelement.tag == 'timeoutSecondsString':
                    timeout_inject['timeout'] = int(subelement.text) / 60
                elif subelement.tag == 'deadlineToleranceInMinutes':
                    timeout_inject['deadline-tolerance'] = int(subelement.text)
                elif subelement.tag == 'timeoutPercentage':
                    timeout_inject['elastic-percentage'] = int(subelement.text)
                elif subelement.tag == 'numberOfBuilds':
                    timeout_inject['elastic-number-builds'] = \
                        int(subelement.text)
                elif subelement.tag == 'timeoutMinutesElasticDefault':
                    timeout_inject['elastic-default-timeout'] = \
                        int(subelement.text)
                elif subelement.tag == 'deadlineTime':
                    timeout_inject['deadline-time'] = subelement.text
                elif subelement.tag == 'failSafeTimeoutDuration':
                    pass
                else:
                    raise NotImplementedError("cannot handle "
                                              "XML %s" % subelement.tag)
        elif element.tag == 'operationList':
            for subelement in element:
                if subelement.tag == FAIL:
                    timeout_inject['fail'] = True
                elif subelement.tag == ABORT:
                    timeout_inject['abort'] = True
                elif subelement.tag == DESC:
                    description = subelement.find('description')
                    if description is not None:
                        timeout_inject['write-description'] = description.text
                else:
                    raise NotImplementedError("cannot handle "
                                              "XML %s" % subelement.tag)
        elif element.tag == 'timeoutEnvVar':
            timeout_inject['timeout-var'] = element.text
        else:
            raise NotImplementedError("cannot handle XML %s" % element.tag)

    parent.append({'timeout': timeout_inject})


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


def secretbuildwrapper(top, parent):
    bindings = []
    for binding in top.find('bindings'):
        params = {}
        if binding.tag == 'org.jenkinsci.plugins.credentialsbinding.impl.ZipFileBinding':
            bindings.append({'zip-file': params})
        elif binding.tag == 'org.jenkinsci.plugins.credentialsbinding.impl.FileBinding':
            bindings.append({'file': params})
        elif binding.tag == 'org.jenkinsci.plugins.credentialsbinding.impl.UsernamePasswordBinding':
            bindings.append({'username-password': params})
        elif binding.tag == 'org.jenkinsci.plugins.credentialsbinding.impl.UsernamePasswordMultiBinding':
            bindings.append({'username-password-separated': params})
        elif binding.tag == 'org.jenkinsci.plugins.credentialsbinding.impl.StringBinding':
            bindings.append({'text': params})
        elif binding.tag == 'com.cloudbees.jenkins.plugins.awscredentials.AmazonWebServicesCredentialsBinding':
            bindings.append({'amazon-web-services', params})
        else:
            raise NotImplementedError("cannot handle XML %s" % binding.tag)

        for child in binding:
            if child.tag == 'credentialsId':
                params['credential-id'] = child.text
            elif child.tag == 'variable':
                params['variable'] = child.text
            elif child.tag == 'usernameVariable':
                params['username'] = child.text
            elif child.tag == 'passwordVariable':
                params['password'] = child.text
            elif child.tag == 'accessKeyVariable':
                params['access-key'] = child.text
            elif child.tag == 'secretKeyVariable':
                params['secret-key'] = child.text
            else:
                raise NotImplementedError("cannot handle XML %s" % binding.tag)

    parent.append({'credentials-binding': bindings})
