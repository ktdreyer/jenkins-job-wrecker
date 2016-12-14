# encoding=utf8
import jenkins_job_wrecker.modules.base
from jenkins_job_wrecker.helpers import get_bool


class Triggers(jenkins_job_wrecker.modules.base.Base):
    component = 'triggers'

    def gen_yml(self, yml_parent, data):
        triggers = []
        for child in data:
            object_name = child.tag.split('.')[-1].lower()
            self.registry.dispatch(self.component, object_name, child, triggers)
        yml_parent.append(['triggers', triggers])


def scmtrigger(top, parent):
    pollscm = {}
    for child in top:
        if child.tag == 'spec':
            pollscm['cron'] = child.text
        elif child.tag == 'ignorePostCommitHooks':
            pollscm['ignore-post-commit-hooks'] = (setting.text == 'true')
        else:
            raise NotImplementedError('cannot handle scm trigger '
                                      'setting %s' % child.tag)

    parent.append({'pollscm': pollscm})


def timertrigger(top, parent):
    parent.append({'timed': top[0].text})


def reversebuildtrigger(top, parent):
    reverse = {}
    for child in top:
        if child.tag == 'upstreamProjects':
            reverse['jobs'] = child.text
        elif child.tag == 'threshold':
            pass    # TODO
        elif child.tag == 'spec':
            pass    # TODO
        else:
            raise NotImplementedError('cannot handle scm trigger '
                                      'setting %s' % child.tag)
    parent.append(reverse)


def gerrittrigger(top, parent):
    pass


def githubpushtrigger(top, parent):
    parent.append('github')


def ghprbtrigger(top, parent):
    ghpr = {}
    for child in top:
        if child.tag == 'spec' or child.tag == 'cron':
            ghpr['cron'] = child.text
        elif child.tag == 'adminlist' and child.text:
            ghpr['admin-list'] = child.text.strip().split('\n')
        elif child.tag == 'allowMembersOfWhitelistedOrgsAsAdmin':
            ghpr['allow-whitelist-orgs-as-admins'] = get_bool(child.text)
        elif child.tag == 'whitelist' and child.text is not None:
            ghpr['white-list'] = child.text.strip().split('\n')
        elif child.tag == 'orgslist' and child.text is not None:
            ghpr['org-list'] = child.text.strip().split('\n')
        elif child.tag == 'buildDescTemplate':
            ghpr['build-desc-template'] = child.text
        elif child.tag == 'triggerPhrase':
            ghpr['trigger-phrase'] = child.text
        elif child.tag == 'onlyTriggerPhrase':
            ghpr['only-trigger-phrase'] = get_bool(child.text)
        elif child.tag == 'useGitHubHooks':
            ghpr['github-hooks'] = get_bool(child.text)
        elif child.tag == 'permitAll':
            ghpr['permit-all'] = get_bool(child.text)
        elif child.tag == 'autoCloseFailedPullRequests':
            ghpr['auto-close-on-fail'] = get_bool(child.text)
        elif child.tag == 'whiteListTargetBranches':
            ghpr['white-list-target-branches'] = []
            for branch in child:
                if branch[0].text is not None:
                    ghpr['white-list-target-branches'].append(branch[0].text.strip())
        elif child.tag == 'gitHubAuthId':
            ghpr['auth-id'] = child.text

    parent.append({'github-pull-request': ghpr})
