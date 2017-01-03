# encoding=utf8
import jenkins_job_wrecker.modules.base


class Scm(jenkins_job_wrecker.modules.base.Base):
    component = 'scm'

    def gen_yml(self, yml_parent, data):
        scm = []
        scm_class = None
        if 'class' in data.attrib:
            if data.attrib['class'] == 'hudson.scm.NullSCM':
                return None
            if data.attrib['class'] == 'org.jenkinsci.plugins.multiplescms.MultiSCM':
                scms = []
                for scm in data[0]:
                    self.gen_yml(yml_parent, scm)
                return
            scm_class = data.attrib['class'].split('.')[-1].lower()
        scm_tag = data.tag.split('.')[-1].lower()
        if scm_tag in self.registry.registry[self.component]:
            self.registry.dispatch(self.component, scm_tag, data, scm)
            yml_parent.append(['scm', scm])
            return
        if scm_class is not None and scm_class in self.registry.registry[self.component]:
            self.registry.dispatch(self.component, scm_class, data, scm)
            yml_parent.append(['scm', scm])
            return
            
        raise NotImplementedError('%s scm not supported' % data.attrib['class'])


def gitscm(top, parent):
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
                if setting.tag == 'credentialsId':
                    git['credentials-id'] = setting.text
                else:
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

    parent.append({'git': git})


def mercurialscm(top, parent):
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

    parent.append({'hg': hg})


def subversionscm(top, parent):
    # Parameters:
    # url (str) - URL of the svn repository
    # basedir (str) - location relative to the workspace root to checkout to (default '.')
    # credentials-id (str) - optional argument to specify the ID of credentials to use
    # repo-depth (str) - Repository depth. Can be one of 'infinity', 'empty',
    # 'files', 'immediates' or 'unknown'. (default 'infinity')
    # ignore-externals (bool) - Ignore Externals. (default false)
    # workspaceupdater (str) - optional argument to specify
    # workspaceupdater -
    # optional argument to specify how to update the workspace (default wipeworkspace)
    # supported values:
    #     wipeworkspace - deletes the workspace before checking out
    #     revertupdate - do an svn revert then an svn update
    #     emulateclean - delete unversioned/ignored files then update
    #     update - do an svn update as much as possible
    # excluded-users (list(str)) - list of users to ignore revisions from when polling for changes (if polling is enabl
    # included-regions (list(str)) - list of file/folders to include (optional)
    # excluded-regions (list(str)) - list of file/folders to exclude (optional)
    # excluded-commit-messages (list(str)) - list of commit messages to exclude (optional)
    # exclusion-revprop-name (str) - revision svn-property to ignore (optional)
    # ignore-property-changes-on-directories (bool) - ignore svn-property only changes of directories (default false)
    # filter-changelog (bool) - If set Jenkins will apply the same inclusion and exclusion patterns for displaying chan
    # repos (list) - list of repositories to checkout (optional)
    # viewvc-url (str) -
    # URL of the svn web interface (optional)
    #     Repo:
    #         url (str) - URL for the repository
    #         basedir (str) - Location relative to the workspace root to checkout to (default '.')
    #         credentials-id - optional ID of credentials to use
    #         repo-depth - Repository depth. Can be one of 'infinity', 'empty', 'files', 'immediates' or 'unknown'. (de
    #         ignore-externals - Ignore Externals. (default false)
    svn = {}

    for child in top:
        if child.tag == 'remote':
            svn['url'] = child.text if child.text else ''
        elif child.tag == 'local':
            svn['basedir'] = child.text if child.text else ''
        elif child.tag == 'credentialsId':
            svn['credentials-id'] = child.text if child.text else ''
        elif child.tag == 'depthOption':
            svn['repo-depth'] = child.text if child.text else ''
        elif child.tag == 'ignoreExternalsOption':
            svn['ignore-externals'] = (child.text == 'true')
        elif child.tag == 'workspaceUpdater':
            # see
            # https://github.com/openstack-infra/jenkins-job-builder/blob/master/jenkins_jobs/modules/scm.py#L835
            if child.attrib['class'] == 'hudson.scm.subversion.CheckoutUpdater':
                svn['workspaceupdater'] = 'wipeworkspace'
            elif child.attrib['class'] == 'hudson.scm.subversion.UpdateWithRevertUpdater':
                svn['workspaceupdater'] = 'revertupdate'
            elif child.attrib['class'] == 'hudson.scm.subversion.UpdateWithCleanUpdater':
                svn['workspaceupdater'] = 'emulateclean'
            elif child.attrib['class'] == 'hudson.scm.subversion.UpdateUpdater':
                svn['workspaceupdater'] = 'update'

        elif child.tag == 'includedRegions':
            svn['included-regions'] = child.text if child.text else ''
        elif child.tag == 'excludedRegions':
            svn['excluded-regions'] = child.text if child.text else ''
        elif child.tag == 'excludedUsers':
            svn['excluded-users'] = child.text if child.text else ''
        elif child.tag == 'excludedCommitMessages':
            svn['excluded-commit-messages'] = child.text if child.text else ''
        elif child.tag == 'excludedRevprop':
            svn['exclusion-revprop-name'] = child.text if child.text else ''
        elif child.tag == 'ignoreDirPropChanges':
            svn['ignore-property-changes-on-directories'] = \
                (child.text == 'true')
        elif child.tag == 'filterChangelog':
            svn['filter-changelog'] = (child.text == 'true')
        elif child.tag == 'locations':
            if len(list(child)) > 0:
                repos = []
                for c in child._children:
                    repo = {}
                    for r in c:
                        if r.tag == 'remote':
                            repo['url'] = r.text if r.text else ''
                        elif r.tag == 'local':
                            repo['basedir'] = r.text if r.text else ''
                        elif r.tag == 'credentialsId':
                            repo['credentials-id'] = r.text if r.text else ''
                        elif r.tag == 'depthOption':
                            repo['repo-depth'] = r.text if r.text else ''
                        elif r.tag == 'ignoreExternalsOption':
                            repo['ignore-externals'] = (r.text == 'true')
                    repos.append(repo)

            svn['repos'] = repos
        else:
            raise NotImplementedError("%s not supported tag in svn scm" % child.tag)

    parent.append({'svn': svn})
