# encoding=utf8
import jenkins_job_wrecker.modules.base
from jenkins_job_wrecker.helpers import get_bool


class Sandbox(jenkins_job_wrecker.modules.base.Base):
    component = 'sandbox'

    def gen_yml(self, yml_parent, data):
        yml_parent.append(['sandbox', data.text])

