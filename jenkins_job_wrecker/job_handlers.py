import logging
import re
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# Handle "<actions/>"
def handle_actions(top):
    # Nothing to do if it's empty.
    # Otherwise...
    if list(top) and len(list(top)) > 0:
        raise NotImplementedError("Don't know how to handle a "
                                  "non-empty <actions> element.")


# Handle "<authToken>tokenvalue</authToken>"
def handle_authtoken(top):
    return [['auth-token', top.text]]


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
        try:
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

            #Throttling
            elif child.tag == 'hudson.plugins.throttleconcurrents.ThrottleJobProperty':
                throttleproperty = handle_throttle_property(child)
                properties.append(throttleproperty)

            # Slack
            elif child.tag == 'jenkins.plugins.slack.SlackNotifier_-SlackJobProperty':
                slackproperty = handle_slack_property(child)
                properties.append(slackproperty)

            elif child.tag == 'jenkins.model.BuildDiscarderProperty':
                discarderproperty = handle_build_discarder_property(child)
                properties.append(discarderproperty)

            # A property we don't know about
            else:
                raise NotImplementedError("cannot handle XML %s" % child.tag)

        except NotImplementedError:
            # Add property information as raw XML
            raw = {}
            raw['xml'] = ET.tostring(child)
            properties.append({'raw':raw})

    return [['properties', properties], ['parameters', parameters]]


# Handle "<jenkins.model.BuildDiscarderProperty>"
def handle_build_discarder_property(top):
    discarder = {}
    mapping = {
        'daysToKeep': 'days-to-keep',
        'numToKeep': 'num-to-keep',
        'artifactDaysToKeep': 'artifact-days-to-keep',
        'artifactNumToKeep': 'artifact-num-to-keep',
    }

    for child in top[0]:
        discarder[mapping[child.tag]] = int(child.text)

    return {'build-discarder': discarder}


# Handle "<com.coravy.hudson.plugins.github.GithubProjectProperty>..."
def handle_github_project_property(top):
    github = {}
    for child in top:
        if child.tag == 'projectUrl':
            github['url'] = child.text
        elif child.tag == 'displayName':
            pass
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
                # Get all the choices
                elif parameter_type == 'choice':
                    choices = []
                    for child in defsetting:
                        if(child.attrib['class'] == 'string-array'):
                            for element in child:
                                choices.append(element.text)
                        else:
                            raise NotImplementedError(child.attrib['class'])
                    value = choices
                # Assume that PyYAML will handle everything else correctly
                else:
                    value = defsetting.text
                parameter_settings[key] = value
            parameters.append({parameter_type: parameter_settings})
    return parameters


def get_bool(txt):
    trues = ['true', 'True', 'Yes', 'yes', '1']
    return txt in trues

def handle_throttle_property(top):
    throttle_ret = {}
    for child in top:
        if child.tag == 'maxConcurrentPerNode':
            throttle_ret['max-per-node'] = child.text
        elif child.tag == 'maxConcurrentTotal':
            throttle_ret['max-total'] = child.text
        elif child.tag == 'throttleOption':
            throttle_ret['option'] = child.text
        elif child.tag == 'throttleEnabled':
            throttle_ret['enabled'] = get_bool(child.text)
        elif child.tag == 'categories':
            throttle_ret['categories'] = []
        elif child.tag == 'configVersion':
            pass # assigned by jjb
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)
    return {'throttle':throttle_ret}

def handle_slack_property(top):
    slack_ret = {}
    notifications = {
        "notifySuccess":"notify-success",
        "notifyAborted":"notify-aborted",
        "notifyNotBuilt":"notify-not-built",
        "notifyUnstable":"notify-unstable",
        "notifyFailure":"notify-failure",
        "notifyBackToNormal":"notify-back-to-normal",
        "notifyRepeatedFailure":"notify-repeated-failure"
    }
    for child in top:
        if child.tag == 'teamDomain':
            slack_ret['team-domain'] = child.text
        elif child.tag == 'token':
            slack_ret['token'] = child.text
        elif child.tag == 'room':
            slack_ret['room'] = child.text
        elif child.tag == 'includeTestSummary':
            slack_ret['include-test-summary'] = (child.text == 'true')
        elif child.tag == 'showCommitList':
            slack_ret['show-commit-list'] = (child.text == 'true')
        elif child.tag == 'includeCustomMessage':
            slack_ret['include-custom-message'] = (child.text == 'true')
        elif child.tag == 'customMessage':
            slack_ret['custom-message'] = child.text
        elif child.tag == 'startNotification':
            slack_ret['start-notification'] = (child.text == 'true')
        elif child.tag in notifications:
            slack_ret[notifications[child.tag]] = (child.text == 'true')
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)
    return {'slack':slack_ret}


# Handle "<scm>..."
def handle_scm(top):
    scm_ret = {}

    try:
        if 'class' in top.attrib:
            if top.attrib['class'] == 'hudson.scm.NullSCM':
                return None

            if top.attrib['class'] == 'org.jenkinsci.plugins.multiplescms.MultiSCM':
                scms = []
                for scm in top[0]:
                    scms.append(handle_scm(scm)[0])
                return scms

        if top.tag == 'hudson.plugins.git.GitSCM' or \
                ('class' in top.attrib and top.attrib['class'] == 'hudson.plugins.git.GitSCM'):
            git = handle_scm_git(top)
            scm_ret = {'git': git}
        elif top.tag == 'hudson.plugins.mercurial.MercurialSCM' or \
                ('class' in top.attrib and top.attrib['class'] == 'hudson.plugins.mercurial.MercurialSCM'):
            hg = handle_scm_hg(top)
            scm_ret = {'hg': hg}
        else:
            raise NotImplementedError("%s scm not supported" % top.attrib['class'])
    except NotImplementedError:
        # Handle scm information as raw XML
        raw = {}
        raw['xml'] = ET.tostring(top)
        scm_ret = {'raw':raw}

    return [['scm', [scm_ret]]]

def handle_scm_hg(top):
    hg = {}

    for child in top:
        if child.tag == 'source':
            hg['url'] = child.text
        elif child.tag == 'credentialsId':
            hg['credentials-id'] = child.text
        elif child.tag == 'revisionType':
            hg['revision-type'] = child.text.lower()
        elif child.tag == 'revision':
            hg['revision'] = child.text
        elif child.tag == 'modules':
            pass
        elif child.tag == 'clean':
            hg['clean'] = (child.text == 'true')
        elif child.tag == 'subdir':
            hg['subdir'] = child.text
        elif child.tag == 'disableChangeLog':
            hg['disable-changelog'] = (child.text == 'true')
        elif child.tag == 'browser' and 'class' in child.attrib:
            browser_class = child.attrib['class']
            if browser_class == 'hudson.plugins.mercurial.browser.BitBucket':
                hg['browser'] = 'bitbucketweb'
            elif browser_class == 'hudson.plugins.mercurial.browser.FishEye':
                hg['browser'] = 'fisheye'
            elif browser_class == 'hudson.plugins.mercurial.browser.GoogleCode':
                hg['browser'] = 'googlecode'
            elif browser_class == 'hudson.plugins.mercurial.browser.HgWeb':
                hg['browser'] = 'hgweb'
            elif browser_class == 'hudson.plugins.mercurial.browser.Kallithea':
                # Not supported by JJB
                raise NotImplementedError("%s is not yet supported by jenkins-job-builder." %
                                          browser_class)
            elif browser_class == 'hudson.plugins.mercurial.browser.KilnHG':
                hg['browser'] = 'kilnhg'
            elif browser_class == 'hudson.plugins.mercurial.browser.RhodeCode':
                hg['browser'] = 'rhodecode'
            elif browser_class == 'hudson.plugins.mercurial.browser.RhodeCodeLegacy':
                hg['browser'] = 'rhodecode-pre-1.2'

            if child.find('url') is not None:
                hg['browser-url'] = child.find('url').text

    return hg

def handle_scm_git(top):
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
            # XXX: blunt hammer: just use the "auto" browser for everything.
            git['browser'] = 'auto'

        elif child.tag == 'extensions':
            for extension in child:
                # hudson.plugins.git.extensions.impl.RelativeTargetDirectory
                if extension.tag == 'hudson.plugins.git.extensions.impl.RelativeTargetDirectory':
                    if len(list(extension)) != 1:
                        # expected <relativeTargetDir>
                        raise NotImplementedError("%s not supported with %i children" % (extension.tag, len(list(extension))))
                    if extension[0].tag != 'relativeTargetDir':
                        raise NotImplementedError("%s XML not supported" % extension[0].tag)
                    git['basedir'] = extension[0].text
                elif extension.tag == 'hudson.plugins.git.extensions.impl.CheckoutOption':
                    if len(list(extension)) != 1:
                        # expected <timeout>
                        raise NotImplementedError("%s not supported with %i children" % (extension.tag, len(list(extension))))
                    if extension[0].tag != 'timeout':
                        raise NotImplementedError("%s XML not supported" % child[0][0].tag)
                    git['timeout'] = extension[0].text
                elif extension.tag == 'hudson.plugins.git.extensions.impl.WipeWorkspace':
                    if len(list(extension)) != 0:
                        raise NotImplementedError("%s not supported with %i children" % (extension.tag, len(list(extension))))
                    git['wipe-workspace'] = True
                elif extension.tag == 'hudson.plugins.git.extensions.impl.LocalBranch':
                    git['local-branch'] = extension[0].text
                elif extension.tag == 'hudson.plugins.git.extensions.impl.PerBuildTag':
                    pass
                else:
                    raise NotImplementedError("%s not supported" % extension.tag)

        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    return git


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
        try:
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
                triggers.append({'pollscm': pollscm})
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
            elif child.tag == 'com.cloudbees.jenkins.GitHubPushTrigger':
                triggers.append('github')
            elif child.tag == 'org.jenkinsci.plugins.ghprb.GhprbTrigger':
                ghpr = {}
                for ghprel in child:
                    tagname = ghprel.tag
                    if tagname == 'spec' or tagname == 'cron':
                        ghpr['cron'] = ghprel.text
                    elif tagname == 'adminlist':
                        ghpr['admin-list'] = ghprel.text.strip().split('\n')
                    elif tagname == 'allowMembersOfWhitelistedOrgsAsAdmin':
                        ghpr['allow-whitelist-orgs-as-admins'] = get_bool(ghprel.text)
                    elif tagname == 'whitelist' and ghprel.text is not None:
                        ghpr['white-list'] = ghprel.text.strip().split('\n')
                    elif tagname == 'orgslist' and ghprel.text is not None:
                        ghpr['org-list'] = ghprel.text.strip().split('\n')
                    elif tagname == 'buildDescTemplate':
                        ghpr['build-desc-template'] = ghprel.text
                    elif tagname == 'triggerPhrase':
                        ghpr['trigger-phrase'] = ghprel.text
                    elif tagname == 'onlyTriggerPhrase':
                        ghpr['only-trigger-phrase'] = get_bool(ghprel.text)
                    elif tagname == 'useGitHubHooks':
                        ghpr['github-hooks'] = get_bool(ghprel.text)
                    elif tagname == 'permitAll':
                        ghpr['permit-all'] = get_bool(ghprel.text)
                    elif tagname == 'autoCloseFailedPullRequests':
                        ghpr['auto-close-on-fail'] = get_bool(ghprel.text)
                    elif tagname == 'whiteListTargetBranches':
                        ghpr['white-list-target-branches'] = []
                        for ghprbranch in ghprel:
                            if ghprbranch[0].text is not None:
                                ghpr['white-list-target-branches'].append(ghprbranch[0].text.strip())
                    elif tagname == 'gitHubAuthId':
                        ghpr['auth-id'] = ghprel.text
                triggers.append({'github-pull-request': ghpr})
            else:
                raise NotImplementedError("cannot handle XML %s" % child.tag)
        except NotImplementedError:
            # Add trigger information as raw XML
            raw = {}
            raw['xml'] = ET.tostring(child)
            triggers.append({'raw':raw})

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

        elif child.tag == 'hudson.matrix.TextAxis':
            axis = {'type': 'user-defined'}
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
        try:
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
                shell = handle_commands(child)
                builders.append({'shell': shell})

            elif child.tag == 'hudson.tasks.BatchFile':
                batch = handle_commands(child)
                builders.append({'batch':batch})

            elif child.tag == 'hudson.tasks.Maven':
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
                builders.append({'maven-target':maven})

            else:
                raise NotImplementedError("cannot handle XML %s" % child.tag)
        except NotImplementedError:
            # Add builder information as raw XML
            raw = {}
            raw['xml'] = ET.tostring(child)
            builders.append({'raw':raw})

    return [['builders', builders]]

def handle_commands(element):
    for shell_element in element:
        # Assumption: there's only one <command> in this
        # <hudson.tasks.Shell>
        if shell_element.tag == 'command':
            # Handle the case where someone creates an empty shell script
            shell = ''
            if shell_element.text is not None:
                shell = str(shell_element.text)
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % shell_element.tag)
    return shell


def handle_publishers(top):
    publishers = []
    for child in top:
        try:
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

            elif child.tag == 'htmlpublisher.HtmlPublisher':
                html_publisher = {}
                element = child[0]
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
                    publishers.append({'html-publisher': html_publisher})


            elif child.tag == 'org.jvnet.hudson.plugins.groovypostbuild.GroovyPostbuildRecorder':
                groovy = {}
                for groovy_element in child:
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
                        continue
                        raise NotImplementedError("cannot handle groovy-postbuild elements")
                publishers.append({'groovy-postbuild':groovy})

            elif child.tag == 'org.jenkins__ci.plugins.flexible__publish.FlexiblePublisher':    # NOQA
                raise NotImplementedError("cannot handle XML %s" % child.tag)

            elif child.tag == 'hudson.plugins.s3.S3BucketPublisher':
                raise NotImplementedError("cannot handle XML %s" % child.tag)
            elif child.tag == 'hudson.plugins.robot.RobotPublisher':
                raise NotImplementedError("cannot handle XML %s" % child.tag)
            elif child.tag == 'jenkins.plugins.publish__over__ssh.BapSshPublisherPlugin':
                raise NotImplementedError("cannot handle XML %s" % child.tag)
            elif child.tag == 'jenkins.plugins.slack.SlackNotifier':
                slacknotifier = {}
                slack_tags = ['teamDomain', 'authToken', 'buildServerUrl', 'room']
                for slack_el in child:
                    if slack_el.tag not in slack_tags:
                        raise NotImplementedError("cannot handle SlackNotifier.%s" % slack_el.tag)
                    slack_yaml_key = re.sub('([A-Z])', r'-\1', slack_el.tag).lower()
                    slacknotifier[slack_yaml_key] = slack_el.text
                publishers.append({'slack': slacknotifier})
            elif child.tag == 'hudson.plugins.postbuildtask.PostbuildTask':
                post_tasks = []
                for pt in child[0]:
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
                publishers.append({'post-tasks': post_tasks})
            elif child.tag == 'hudson.plugins.ws__cleanup.WsCleanup':
                cleanup = {'include': [], 'exclude': [], 'clean-if': []}
                for cleanupel in child:
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
                publishers.append({'workspace-cleanup': cleanup})
            else:
                raise NotImplementedError("cannot handle XML %s" % child.tag)
        except NotImplementedError:
            # Add publisher information as raw XML
            raw = {}
            raw['xml'] = ET.tostring(child)
            publishers.append({'raw':raw})

    return [['publishers', publishers]]


def handle_buildwrappers(top):
    wrappers = []
    for child in top:
        try:
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

            elif child.tag == 'hudson.plugins.ws__cleanup.PreBuildCleanup':
                preclean = {}
                preclean_patterns = {'include': '', 'exclude': ''}
                for element in child:
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
                    if len(preclean_patterns[rule]) > 0:
                        preclean[rule] = preclean_patterns[rule]

                if len(preclean) > 0:
                    wrappers.append({'workspace-cleanup': preclean})
                else:
                    wrappers.append('workspace-cleanup')

            elif child.tag == 'org.jenkinsci.plugins.xvfb.XvfbBuildWrapper':
                xvfb = {}
                for element in child:
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

                wrappers.append({'xvfb': xvfb})

            elif child.tag == 'com.michelin.cio.hudson.plugins.maskpasswords.MaskPasswordsBuildWrapper':
                wrappers.append('mask-passwords')

            else:
                raise NotImplementedError("cannot handle XML %s" % child.tag)
        except NotImplementedError:
            # Add wrapper information as raw XML
            raw = {}
            raw['xml'] = ET.tostring(child)
            wrappers.append({'raw':raw})

    return [['wrappers', wrappers]]


def handle_executionstrategy(top):
    strategy = {}
    for child in top:

        if child.tag == 'runSequentially':
            strategy['run-sequentially'] = (child.text == 'true')
        elif child.tag == 'sorter':
            # Is there anything but NOOP?
            pass
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

def handle_jdk(top):
    return [['jdk',top.text]]
