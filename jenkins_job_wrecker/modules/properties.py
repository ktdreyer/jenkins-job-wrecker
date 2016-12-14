# encoding=utf8
import jenkins_job_wrecker.modules.base
from jenkins_job_wrecker.helpers import get_bool


class Properties(jenkins_job_wrecker.modules.base.Base):
    component = 'properties'

    def gen_yml(self, yml_parent, data):
        properties = []
        parameters = []
        for child in data:
            object_name = child.tag.split('.')[-1].lower()
            object_name = object_name.replace('-', '').replace('_', '')
            if object_name == 'parametersdefinitionproperty':
                self.registry.dispatch(self.component, object_name, child, parameters)
                continue
            self.registry.dispatch(self.component, object_name, child, properties)

        yml_parent.append(['properties', properties])
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


def parametersdefinitionproperty(top, parent):
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
                key = {'defaultValue': 'default'}.get(defsetting.tag, defsetting.tag)
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
                    for sub_setting in defsetting:
                        if(sub_setting.attrib['class'] == 'string-array'):
                            for element in sub_setting:
                                choices.append(element.text)
                        else:
                            raise NotImplementedError(sub_setting.attrib['class'])
                    value = choices
                # Assume that PyYAML will handle everything else correctly
                else:
                    value = defsetting.text
                parameter_settings[key] = value
            parent.append({parameter_type: parameter_settings})


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
