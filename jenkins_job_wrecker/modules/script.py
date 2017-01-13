# encoding=utf8
import jenkins_job_wrecker.modules.base
from jenkins_job_wrecker.helpers import get_bool


class Script(jenkins_job_wrecker.modules.base.Base):
    component = 'script'

    def gen_yml(self, yml_parent, data):
        yml_parent.append(['script', data.text])

