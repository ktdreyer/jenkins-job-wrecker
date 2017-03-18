# encoding=utf8
import jenkins_job_wrecker.modules.base
from jenkins_job_wrecker.helpers import get_bool,gen_raw

PARAMETER_MAPPER = {
    'stringparameterdefinition': 'string',
    'booleanparameterdefinition': 'bool',
    'choiceparameterdefinition': 'choice',
    'textparameterdefinition': 'text',
    'fileparameterdefinition': 'file',}


class Properties(jenkins_job_wrecker.modules.base.Base):
    component = 'properties'

    def gen_yml(self, yml_parent, data):
        parameters = []
        properties = []
        for child in data:
            object_name = child.tag.split('.')[-1].lower()
            object_name = object_name.replace('-', '').replace('_', '')
            if object_name == 'parametersdefinitionproperty':
                self.registry.dispatch(self.component, 'parameters', child, parameters)
                continue
            self.registry.dispatch(self.component, object_name, child, properties)

        if len(properties) > 0:
            yml_parent.append(['properties', properties])
        if len(parameters) > 0:
            yml_parent.append(['parameters', parameters])


def githubprojectproperty(top, parent):
    github = {}
    for child in top:
        if child.tag == 'projectUrl':
            github['url'] = child.text
        elif child.tag == 'displayName':
            pass
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    parent.append({'github': github})


def parameters(top, parent):
    for params in top:
        if params.tag != 'parameterDefinitions':
            raise NotImplementedError("cannot handle XML %s" % params.tag)
        for param in params:
            param_name = param.tag.split('.')[-1].lower()
            if param_name not in PARAMETER_MAPPER:
                gen_raw(param,parent)
                continue
            param_type = PARAMETER_MAPPER[param_name]
            parameter = {}
            for setting in param:
                key = {'defaultValue': 'default'}.get(setting.tag, setting.tag)
                if setting.text is None:
                    parameter[key] = ''
                elif setting.text == 'true' or setting.text == 'false':
                    parameter[key] = (setting.text == 'true')
                elif param_type == 'choice' and setting.tag == 'choices':
                    choices = []
                    for sub_setting in setting:
                        if(sub_setting.attrib['class'] == 'string-array'):
                            for item in sub_setting:
                                choices.append(item.text)
                        else:
                            raise NotImplementedError(sub_setting.attrib['class'])
                    parameter[key] = choices
                else:
                    parameter[key] = setting.text
            parent.append({param_type: parameter})


def throttlejobproperty(top, parent):
    throttle = {}
    for child in top:
        if child.tag == 'maxConcurrentPerNode':
            throttle['max-per-node'] = child.text
        elif child.tag == 'maxConcurrentTotal':
            throttle['max-total'] = child.text
        elif child.tag == 'throttleOption':
            throttle['option'] = child.text
        elif child.tag == 'throttleEnabled':
            throttle['enabled'] = get_bool(child.text)
        elif child.tag == 'categories':
            throttle['categories'] = []
        elif child.tag == 'configVersion':
            pass # assigned by jjb
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    parent.append({'throttle':throttle})


def slacknotifierslackjobproperty(top, parent):
    slack = {}
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
            slack['team-domain'] = child.text
        elif child.tag == 'token':
            slack['token'] = child.text
        elif child.tag == 'room':
            slack['room'] = child.text
        elif child.tag == 'includeTestSummary':
            slack['include-test-summary'] = (child.text == 'true')
        elif child.tag == 'showCommitList':
            slack['show-commit-list'] = (child.text == 'true')
        elif child.tag == 'includeCustomMessage':
            slack['include-custom-message'] = (child.text == 'true')
        elif child.tag == 'customMessage':
            slack['custom-message'] = child.text
        elif child.tag == 'startNotification':
            slack['start-notification'] = (child.text == 'true')
        elif child.tag in notifications:
            slack[notifications[child.tag]] = (child.text == 'true')
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    parent.append({'slack': slack})


def builddiscarderproperty(top, parent):
    discarder = {}
    mapping = {'daysToKeep': 'days-to-keep',
               'numToKeep': 'num-to-keep',
               'artifactDaysToKeep': 'artifact-days-to-keep',
               'artifactNumToKeep': 'artifact-num-to-keep'}
    for child in top[0]:
        discarder[mapping[child.tag]] = int(child.text)

    parent.append({'build-discarder': discarder})
