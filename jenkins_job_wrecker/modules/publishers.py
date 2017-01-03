# encoding=utf8
import jenkins_job_wrecker.modules.base
from jenkins_job_wrecker.helpers import get_bool


class Publishers(jenkins_job_wrecker.modules.base.Base):
    component = 'publishers'

    def gen_yml(self, yml_parent, data):
        publishers = []
        for child in data:
            object_name = child.tag.split('.')[-1].lower()
            self.registry.dispatch(self.component, object_name, child, publishers)
        yml_parent.append(['publishers', publishers])


def artifactarchiver(top, parent):
    archive = {}
    for element in top:
        if element.tag == 'artifacts':
            archive['artifacts'] = element.text
        elif element.tag == 'allowEmptyArchive':
            archive['allow-empty'] = (element.text == 'true')
        elif element.tag == 'fingerprint':
            archive['fingerprint'] = (element.text == 'true')
        elif element.tag == 'onlyIfSuccessful':
            # only-if-success first available in JJB 1.3.0
            archive['only-if-success'] = (element.text == 'true')
        elif element.tag == 'defaultExcludes':
            # default-excludes is not yet available in JJB master
            archive['default-excludes'] = (element.text == 'true')
        elif element.tag == 'latestOnly':
            archive['latest-only'] = (element.text == 'true')
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % element.tag)

    parent.append({'archive': archive})


def descriptionsetterpublisher(top, parent):
    setter = {}
    for element in top:
        if element.tag == 'regexp':
            setter['regexp'] = element.text
        elif element.tag == 'regexpForFailed':
            setter['regexp-for-failed'] = element.text
        elif element.tag == 'setForMatrix':
            setter['set-for-matrix'] = (element.text == 'true')
        elif element.tag == 'description':
            setter['description'] = element.text
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % element.tag)

    parent.append({'description-setter': setter})


def fingerprinter(top, parent):
    fingerprint = {}
    for element in top:
        if element.tag == 'targets':
            fingerprint['files'] = element.text
        elif element.tag == 'recordBuildArtifacts':
            fingerprint['record-artifacts'] = (element.text == 'true')
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % element.tag)
    parent.append({'fingerprint': fingerprint})


def extendedemailpublisher(top, parent):
    ext_email = {}
    for element in top:
        if element.tag == 'recipientList':
            ext_email['recipients'] = element.text
        elif element.tag == 'replyTo':
            ext_email['reply-to'] = element.text
        elif element.tag == 'contentType':
            ext_email['content-type'] = element.text
        elif element.tag == 'defaultSubject':
            ext_email['subject'] = element.text
        elif element.tag == 'defaultContent':
            ext_email['body'] = element.text
        elif element.tag in ['attachBuildLog', 'compressBuildLog']:
            ext_email['attach-build-log'] = (element.text == 'true')
        elif element.tag == 'attachmentsPattern':
            ext_email['attachment'] = element.text
        elif element.tag in ['saveOutput', 'disabled']:
            pass
        elif element.tag == 'preBuild':
            ext_email['pre-build'] = (element.text == 'true')
        elif element.tag == 'presendScript':
            ext_email['presend-script'] = element.text
        elif element.tag == 'sendTo':
            ext_email['send-to'] = element.text
        elif element.tag == 'configuredTriggers':
            print "IGNORED configuredTriggers in email-ext"
        else:
            raise NotImplementedError("cannot handle "
                                          "XML %s" % element.tag)

    parent.append({'email-ext': ext_email})


def junitresultarchiver(top, parent):
    junit_publisher = {}
    for element in top:
        if element.tag == 'testResults':
            junit_publisher['results'] = element.text
        elif element.tag == 'keepLongStdio':
            junit_publisher['keep-long-stdio'] = \
                (element.text == 'true')
        elif element.tag == 'healthScaleFactor':
            junit_publisher['health-scale-factor'] = element.text
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % element.tag)
    parent.append({'junit': junit_publisher})


def buildtrigger(top, parent):
    build_trigger = {}

    for element in top:
        for sub in element:
            if sub.tag == 'hudson.plugins.parameterizedtrigger.BuildTriggerConfig':     # NOQA
                for config in sub:
                    if config.tag == 'projects':
                        build_trigger['project'] = config.text
                    elif config.tag == 'condition':
                        build_trigger['condition'] = config.text
                    elif config.tag == 'triggerWithNoParameters':
                        build_trigger['trigger-with-no-params'] = \
                            (config.text == 'true')
                    elif config.tag == 'configs':
                        pass
                    else:
                        raise NotImplementedError("cannot handle "
                                                  "XML %s" % config.tag)

    parent.append({'trigger-parameterized-builds': build_trigger})


def mailer(top, parent):
    email_settings = {}
    for element in top:

        if element.tag == 'recipients':
            email_settings['recipients'] = element.text
        elif element.tag == 'dontNotifyEveryUnstableBuild':
            email_settings['notify-every-unstable-build'] = \
                (element.text == 'true')
        elif element.tag == 'sendToIndividuals':
            email_settings['send-to-individuals'] = \
                (element.text == 'true')
        else:
            raise NotImplementedError("cannot handle "
                                      "email %s" % element.tag)
    parent.append({'email': email_settings})


def htmlpublisher(top, parent):
    html_publisher = {}
    element = top[0]
    if element.tag != 'reportTargets':
        raise NotImplementedError("Cannot handle XML %s" % element.tag)
    for subelement in element:
        if subelement.tag != 'htmlpublisher.HtmlPublisherTarget':
            raise NotImplementedError("Cannot handle XML %s" % element.tag)
        for config in subelement:
            if config.tag == 'reportName':
                html_publisher['name'] = config.text
            if config.tag == 'reportDir':
                html_publisher['dir'] = config.text
            if config.tag == 'reportFiles':
                html_publisher['files'] = config.text
            if config.tag == 'keepAll':
                html_publisher['keep-all'] = (config.text == 'true')
            if config.tag == 'allowMissing':
                html_publisher['allow-missing'] = (config.text == 'true')
            if config.tag == 'alwaysLinkToLastBuild':
                html_publisher['link-to-last-build'] = (config.text == 'true')
            if config.tag == 'wrapperName':
                # Apparently, older versions leakded this wrapper name
                # to the job configuration.
                pass

    if len(html_publisher) > 0:
        parent.append({'html-publisher': html_publisher})


def groovypostbuildrecorder(top, parent):
    groovy = {}
    for groovy_element in top:
        if groovy_element.tag == 'groovyScript':
            groovy['script'] = groovy_element.text
        elif groovy_element.tag == 'classpath':
            classpaths = []
            for child1 in groovy_element:
                for child2 in child1:
                    if child2.tag == 'path':
                        classpaths.append(child2.text)
            groovy['classpath'] = classpaths;
        else:
            continue # WTF is this?
            raise NotImplementedError("cannot handle groovy-postbuild elements")
    parent.append({'groovy-postbuild':groovy})


def slacknotifier(top, parent):
    slacknotifier = {}
    slack_tags = ['teamDomain', 'authToken', 'buildServerUrl', 'room']
    for slack_el in top:
        if slack_el.tag not in slack_tags:
            raise NotImplementedError("cannot handle SlackNotifier.%s" % slack_el.tag)
        slack_yaml_key = re.sub('([A-Z])', r'-\1', slack_el.tag).lower()
        slacknotifier[slack_yaml_key] = slack_el.text
    parent.append({'slack': slacknotifier})


def postbuildtask(top, parent):
    post_tasks = []
    for pt in top[0]:
        post_task = {}
        for ptel in pt:
            if ptel.tag == 'logTexts':
                matches = []
                for logtext in ptel:
                    match = {}
                    for logtextel in logtext:
                        if logtextel.tag == 'logText':
                            match['log-text'] = logtextel.text
                        elif logtextel.tag == 'operator':
                            match['operator'] = logtextel.text
                    matches.append(match)
                post_task['matches'] = matches
            elif ptel.tag == 'EscalateStatus':
                post_task['escalate-status'] = get_bool(ptel.text)
            elif ptel.tag == 'RunIfJobSuccessful':
                post_task['run-if-job-successful'] = get_bool(ptel.text)
            elif ptel.tag == 'script':
                post_task['script'] = ptel.text
        post_tasks.append(post_task)
    parent.append({'post-tasks': post_tasks})


def wscleanup(top, parent):
    cleanup = {'include': [], 'exclude': [], 'clean-if': []}
    for cleanupel in top:
        if cleanupel.tag == 'patterns':
            for pattern in cleanupel:
                pattern_glob = None
                pattern_type = None
                for patternel in pattern:
                    if patternel.tag == 'pattern':
                        pattern_glob = patternel.text
                    elif patternel.tag == 'type':
                        pattern_type = patternel.text
                cleanup[pattern_type.lower()].append(pattern_glob)
        elif cleanupel.tag == 'deleteDirs':
            cleanup['dirmatch'] = get_bool(cleanupel.text)
        elif cleanupel.tag == 'cleanWhenSuccess':
            cleanup['clean-if'].append({'success': get_bool(cleanupel.text)})
        elif cleanupel.tag == 'cleanWhenUnstable':
            cleanup['clean-if'].append({'unstable': get_bool(cleanupel.text)})
        elif cleanupel.tag == 'cleanWhenFailure':
            cleanup['clean-if'].append({'failure': get_bool(cleanupel.text)})
        elif cleanupel.tag == 'cleanWhenNotBuilt':
            cleanup['clean-if'].append({'not-built': get_bool(cleanupel.text)})
        elif cleanupel.tag == 'cleanWhenAborted':
            cleanup['clean-if'].append({'aborted': get_bool(cleanupel.text)})
        elif cleanupel.tag == 'notFailBuild':
            cleanup['fail-build'] = not get_bool(cleanupel.text)
        elif cleanupel.tag == 'cleanupMatrixParent':
            cleanup['clean-parent'] = get_bool(cleanupel.text)
    parent.append({'workspace-cleanup': cleanup})
