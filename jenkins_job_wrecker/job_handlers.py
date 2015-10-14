import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# Handle "<actions/>"
def handle_actions(top):
    # Nothing to do if it's empty.
    # Otherwise...
    if list(top) and len(list(top)) > 0:
        raise NotImplementedError("Don't know how to handle a "
                                  "non-empty <actions> element.")


# Handle "<description>my cool job</description>"
def handle_description(top):
    return [['description', top.text]]


# Handle "<keepDependencies>false</keepDependencies>"
def handle_keepdependencies(top):
    # JJB cannot handle any other value than false, here.
    # There is no corresponding YAML option.
    return None


# Handle "<properties>..."
def handle_properties(top):
    properties = []
    parameters = []
    for child in top:
        # GitHub
        if child.tag == 'com.coravy.hudson.plugins.github.GithubProjectProperty':   # NOQA
            github = handle_github_project_property(child)
            properties.append(github)
        # Parameters
        elif child.tag == 'hudson.model.ParametersDefinitionProperty':
            parametersdefs = handle_parameters_property(child)
            for pd in parametersdefs:
                parameters.append(pd)
        # Parameters
        elif child.tag == 'com.sonyericsson.rebuild.RebuildSettings':
            # latest version of JJB (1.3.0 at the moment) doesn't support this.
            continue
        # A property we don't know about
        else:
            print "cannot handle XML %s" % child.tag
    return [['properties', properties], ['parameters', parameters]]


# Handle "<com.coravy.hudson.plugins.github.GithubProjectProperty>..."
def handle_github_project_property(top):
    github = {}
    for child in top:
        if child.tag == 'projectUrl':
            github['url'] = child.text
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)
    return {'github': github}


# Handle "<hudson.model.ParametersDefinitionProperty>..."
def handle_parameters_property(top):
    parameters = []
    for parameterdefs in top:
        if parameterdefs.tag != 'parameterDefinitions':
            raise NotImplementedError("cannot handle "
                                      "XML %s" % parameterdefs.tag)
        for parameterdef in parameterdefs:
            if parameterdef.tag == 'hudson.model.StringParameterDefinition':
                parameter_type = 'string'
            elif parameterdef.tag == 'hudson.model.BooleanParameterDefinition':
                parameter_type = 'bool'
            elif parameterdef.tag == 'hudson.model.ChoiceParameterDefinition':
                parameter_type = 'choice'
                raise NotImplementedError(parameterdef.tag)
            else:
                raise NotImplementedError(parameterdef.tag)

            parameter_settings = {}
            for defsetting in parameterdef:
                key = {
                    'defaultValue': 'default',
                }.get(defsetting.tag, defsetting.tag)
                # If the XML had a blank string, don't pass None to PyYAML,
                # because PyYAML will translate this as "null". Just use a
                # blank string to be safe.
                if defsetting.text is None:
                    value = ''
                # If the XML has a value of "true" or "false", we shouldn't
                # treat the value as a string. Use native Python booleans
                # so PyYAML will not quote the values as strings.
                elif defsetting.text == 'true':
                    value = True
                elif defsetting.text == 'false':
                    value = False
                # Assume that PyYAML will handle everything else correctly
                else:
                    value = defsetting.text
                parameter_settings[key] = value
            parameters.append({parameter_type: parameter_settings})
    return parameters


# Handle "<scm>..."
def handle_scm(top):
    if 'class' in top.attrib:
        if top.attrib['class'] == 'hudson.scm.NullSCM':
            return None

        if top.attrib['class'] == 'org.jenkinsci.plugins.multiplescms.MultiSCM':
            scms = []
            for scm in top[0]:
                scms.append(handle_scm(scm)[0])
            return scms

    if top.tag != 'hudson.plugins.git.GitSCM' and \
            top.attrib['class'] != 'hudson.plugins.git.GitSCM':
        raise NotImplementedError("%s scm not supported" % top.attrib['class'])

    git = {}

    for child in top:

        if child.tag == 'configVersion':
            continue    # we don't care

        elif child.tag == 'userRemoteConfigs':
            if len(list(child)) != 1:
                # expected "hudson.plugins.git.UserRemoteConfig" tag
                raise NotImplementedError("%s not supported with %i "
                                          "children" % (child.tag,
                                                        len(list(child))))

            for setting in child[0]:
                git[setting.tag] = setting.text

        elif child.tag == 'gitTool':
            git['git-tool'] = child.text

        elif child.tag == 'excludedUsers':
            if child.text:
                users = child.text.split()
                git['excluded-users'] = users

        elif child.tag == 'buildChooser':
            if child.attrib['class'] == \
                    'hudson.plugins.git.util.DefaultBuildChooser':
                continue
            else:
                # see JJB's jenkins_jobs/modules/scm.py
                # for other build choosers
                raise NotImplementedError("%s build "
                                          "chooser" % child.attrib['class'])

        elif child.tag == 'disableSubmodules':
            # 'false' is the default and needs no explict YAML.
            if child.text == 'true':
                raise NotImplementedError("TODO: %s" % child.tag)

        elif child.tag == 'recursiveSubmodules':
            # 'false' is the default and needs no explict YAML.
            if child.text == 'true':
                raise NotImplementedError("TODO: %s" % child.tag)

        elif child.tag == 'authorOrCommitter':
            # 'false' is the default and needs no explict YAML.
            if child.text == 'true':
                git['use-author'] = True

        elif child.tag == 'useShallowClone':
            # 'false' is the default and needs no explict YAML.
            if child.text == 'true':
                git['shallow-clone'] = True

        elif child.tag == 'ignoreNotifyCommit':
            # 'false' is the default and needs no explict YAML.
            if child.text == 'true':
                git['ignore-notify'] = True

        elif child.tag == 'wipeOutWorkspace':
            git['wipe-workspace'] = (child.text == 'true')

        elif child.tag == 'skipTag':
            # 'false' is the default and needs no explict YAML.
            if child.text == 'true':
                git['skip-tag'] = True

        elif child.tag == 'pruneBranches':
            # 'false' is the default and needs no explict YAML.
            if child.text == 'true':
                git['prune'] = True

        elif child.tag == 'remotePoll':
            # 'false' is the default and needs no explict YAML.
            if child.text == 'true':
                git['fastpoll'] = True

        elif child.tag == 'relativeTargetDir':
            # If it's empty, no explicit 'basedir' YAML needed.
            if child.text:
                git['basedir'] = child.text

        elif child.tag == 'reference':
            # If it's empty, we're good
            if child.text or len(list(child)) > 0:
                raise NotImplementedError(child.tag)

        elif child.tag == 'gitConfigName':
            # If it's empty, we're good
            if child.text or len(list(child)) > 0:
                raise NotImplementedError(child.tag)

        elif child.tag == 'gitConfigEmail':
            # If it's empty, we're good
            if child.text or len(list(child)) > 0:
                raise NotImplementedError(child.tag)

        elif child.tag == 'scmName':
            # If it's empty, we're good
            if child.text or len(list(child)) > 0:
                raise NotImplementedError(child.tag)

        elif child.tag == 'branches':
            if child[0][0].tag != 'name':
                raise NotImplementedError("%s XML not supported"
                                          % child[0][0].tag)
            branches = []
            for item in child:
                for branch in item:
                    branches.append(branch.text)
            git['branches'] = branches

        elif child.tag == 'doGenerateSubmoduleConfigurations':
            if len(list(child)) != 0:
                raise NotImplementedError("%s not supported with %i children"
                                          % (child.tag, len(list(child))))
            # JJB doesn't handle this element anyway. Just continue on.
            continue

        elif child.tag == 'submoduleCfg':
            if len(list(child)) > 0:
                raise NotImplementedError("%s not supported with %i children"
                                          % (child.tag, len(list(child))))

        elif child.tag == 'browser':
            if child.text or len(list(child)) > 0:
                raise NotImplementedError(child.tag)

        elif child.tag == 'extensions':
            if len(list(child)) == 0 or not list(child[0]):
                # This is just an empty <extensions/>. We can skip it.
                continue
            if len(list(child)) != 1:
                # hudson.plugins.git.extensions.impl.RelativeTargetDirectory
                raise NotImplementedError("%s not supported with %i children"
                                          % (child.tag, len(list(child))))
            if len(list(child[0])) != 1:
                print list(child[0])
                # expected relativeTargetDir
                raise NotImplementedError("%s not supported with %i children"
                                          % (child[0].tag, len(list(child[0]))))
            if child[0][0].tag != 'relativeTargetDir':
                raise NotImplementedError("%s XML not supported"
                                          % child[0][0].tag)
            git['basedir'] = child[0][0].text

        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)
    return [['scm', [{'git': git}]]]


# Handle "<canRoam>true</canRoam>"
def handle_canroam(top):
    # JJB doesn't have an explicit YAML setting for this; instead, it
    # infers it from the "node" parameter. So there's no need to handle the
    # XML here.
    return None


# Handle "<disabled>false</disabled>"
def handle_disabled(top):
    return [['disabled', top.text == 'true']]


# Handle "<blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>" NOQA
def handle_blockbuildwhendownstreambuilding(top):
    return [['block-downstream', top.text == 'true']]


# Handle "<blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>" NOQA
def handle_blockbuildwhenupstreambuilding(top):
    return [['block-upstream', top.text == 'true']]


def handle_triggers(top):
    triggers = []

    for child in top:
        if child.tag == 'hudson.triggers.SCMTrigger':
            pollscm = {}
            for setting in child:
                if setting.tag == 'spec':
                    pollscm['cron'] = setting.text
                elif setting.tag == 'ignorePostCommitHooks':
                    pollscm['ignore-post-commit-hooks'] = \
                        (setting.text == 'true')
                else:
                    raise NotImplementedError("cannot handle scm trigger "
                                              "setting %s" % setting.tag)
            triggers.append(pollscm)
        elif child.tag == 'hudson.triggers.TimerTrigger':
            timed_trigger = {}
            timed_trigger['timed'] = child[0].text
            triggers.append(timed_trigger)
        elif child.tag == 'jenkins.triggers.ReverseBuildTrigger':
            reverse = {}
            for setting in child:
                if setting.tag == 'upstreamProjects':
                    reverse['jobs'] = setting.text
                elif setting.tag == 'threshold':
                    pass    # TODO
                elif setting.tag == 'spec':
                    pass    # TODO
                else:
                    raise NotImplementedError("cannot handle reverse trigger "
                                              "setting %s" % setting.tag)
            triggers.append(reverse)
        elif child.tag == 'com.sonyericsson.hudson.plugins.gerrit.trigger.hudsontrigger.GerritTrigger':     # NOQA
            # Skip for now
            pass
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)
    return [['triggers', triggers]]


def handle_concurrentbuild(top):
    return [['concurrent', top.text == 'true']]


def handle_axes(top):
    axes = []
    for child in top:

        if child.tag == 'hudson.matrix.LabelExpAxis':
            axis = {'type': 'label-expression'}
            for axis_element in child:
                if axis_element.tag == 'name':
                    axis['name'] = axis_element.text
                if axis_element.tag == 'values':
                    values = []
                    for value_element in axis_element:
                        values.append(value_element.text)
                    axis['values'] = values
            axes.append({'axis': axis})

        elif child.tag == 'hudson.matrix.LabelAxis':
            axis = {'type': 'slave'}
            for axis_element in child:
                if axis_element.tag == 'name':
                    axis['name'] = axis_element.text
                if axis_element.tag == 'values':
                    values = []
                    for value_element in axis_element:
                        values.append(value_element.text)
                    axis['values'] = values
            axes.append({'axis': axis})

        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    return [['axes', axes]]


def handle_builders(top):
    builders = []
    for child in top:

        if child.tag == 'hudson.plugins.copyartifact.CopyArtifact':
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
            builders.append({'copyartifact': copyartifact})

        elif child.tag == 'hudson.tasks.Shell':
            for shell_element in child:
                # Assumption: there's only one <command> in this
                # <hudson.tasks.Shell>
                if shell_element.tag == 'command':
                    shell = shell_element.text
                else:
                    raise NotImplementedError("cannot handle "
                                              "XML %s" % shell_element.tag)
            builders.append({'shell': shell})

        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    return [['builders', builders]]


def handle_publishers(top):
    publishers = []
    for child in top:

        if child.tag == 'hudson.tasks.ArtifactArchiver':
            archive = {}
            for element in child:
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

            publishers.append({'archive': archive})

        elif child.tag == 'hudson.plugins.descriptionsetter.DescriptionSetterPublisher':  # NOQA
            setter = {}
            for element in child:
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

            publishers.append({'description-setter': setter})

        elif child.tag == 'hudson.tasks.Fingerprinter':
            fingerprint = {}
            for element in child:
                if element.tag == 'targets':
                    fingerprint['files'] = element.text
                elif element.tag == 'recordBuildArtifacts':
                    fingerprint['record-artifacts'] = (element.text == 'true')
                else:
                    raise NotImplementedError("cannot handle "
                                              "XML %s" % element.tag)
            publishers.append({'fingerprint': fingerprint})

        elif child.tag == 'hudson.plugins.emailext.ExtendedEmailPublisher':
            ext_email = {}
            for element in child:
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

            publishers.append({'email-ext': ext_email})

        elif child.tag == 'hudson.tasks.junit.JUnitResultArchiver':
            junit_publisher = {}
            for element in child:
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
            publishers.append({'junit': junit_publisher})

        elif child.tag == 'hudson.plugins.parameterizedtrigger.BuildTrigger':
            build_trigger = {}

            for element in child:
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

            publishers.append({'trigger-parameterized-builds': build_trigger})

        elif child.tag == 'hudson.tasks.Mailer':
            email_settings = {}
            for element in child:

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
            publishers.append({'email': email_settings})

        elif child.tag == 'org.jenkins__ci.plugins.flexible__publish.FlexiblePublisher':    # NOQA
            raise NotImplementedError("cannot handle XML %s" % child.tag)

        elif child.tag == 'hudson.plugins.s3.S3BucketPublisher':
            raise NotImplementedError("cannot handle XML %s" % child.tag)
        elif child.tag == 'hudson.plugins.robot.RobotPublisher':
            raise NotImplementedError("cannot handle XML %s" % child.tag)

        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    return [['publishers', publishers]]


def handle_buildwrappers(top):
    wrappers = []
    for child in top:

        if child.tag == 'EnvInjectPasswordWrapper':
            inject = {}
            for element in child:
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
            wrappers.append({'inject': inject})

        elif child.tag == 'EnvInjectBuildWrapper':
            build_inject = {}
            for element in child:
                if element.tag == 'info':
                    for subelement in element:
                        if subelement.tag == 'propertiesFilePath':
                            build_inject['properties-file'] = subelement.text
                        if subelement.tag == 'loadFilesFromMaster':
                            pass
                else:
                    raise NotImplementedError("cannot handle "
                                              "XML %s" % element.tag)
            wrappers.append({'inject': build_inject})

        elif child.tag == 'hudson.plugins.build__timeout.BuildTimeoutWrapper':
            pass

        elif child.tag == 'hudson.plugins.ansicolor.AnsiColorBuildWrapper':
            wrappers.append({'ansicolor': {'colormap': 'xterm'}})

        elif child.tag == 'com.cloudbees.jenkins.plugins.sshagent.SSHAgentBuildWrapper':    # NOQA
            ssh_agents = {}
            for element in child:
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
            wrappers.append({'ssh-agent-credentials': ssh_agents})

        elif child.tag == 'org.jenkinsci.plugins.buildnamesetter.BuildNameSetter':  # NOQA
            wrappers.append({'build-name': {'name': child[0].text}})

        elif child.tag == 'hudson.plugins.timestamper.TimestamperBuildWrapper':
            wrappers.append('timestamps')

        else:
            print child
            raise NotImplementedError("cannot handle XML %s" % child.tag)
    return [['wrappers', wrappers]]


def handle_executionstrategy(top):
    strategy = {}
    for child in top:

        if child.tag == 'runSequentially':
            strategy['run-sequentially'] = (child.text == 'true')
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    return [['execution-strategy', strategy]]


# Handle "<logrotator>...</logrotator>"'
def handle_logrotator(top):
    logrotate = {}
    for child in top:

        if child.tag == 'daysToKeep':
            logrotate['daysToKeep'] = child.text
        elif child.tag == 'numToKeep':
            logrotate['numToKeep'] = child.text
        elif child.tag == 'artifactDaysToKeep':
            logrotate['artifactDaysToKeep'] = child.text
        elif child.tag == 'artifactNumToKeep':
            logrotate['artifactNumToKeep'] = child.text
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    return [['logrotate', logrotate]]


# Handle "<combinationFilter>a != &quot;b&quot;</combinationFilter>"
def handle_combinationfilter(top):
    return [['combination-filter', top.text]]


# Handle "<assignedNode>server.example.com</assignedNode>"
def handle_assignednode(top):
    return [['node', top.text]]


# Handle "<displayName>my cool job</displayName>"
def handle_displayname(top):
    return [['display-name', top.text]]


# Handle "<quietPeriod>5</quietPeriod>"
def handle_quietperiod(top):
    return [['quiet-period', top.text]]


# Handle "<scmCheckoutRetryCount>8</scmCheckoutRetryCount>"
def handle_scmcheckoutretrycount(top):
    return [['retry-count', top.text]]


def handle_customworkspace(top):
    return [['workspace', top.text]]
