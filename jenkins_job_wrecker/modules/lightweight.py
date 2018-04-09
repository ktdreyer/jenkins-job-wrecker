# encoding=utf8
import jenkins_job_wrecker.modules.base
from jenkins_job_wrecker.helpers import get_bool


class Lightweight(jenkins_job_wrecker.modules.base.Base):
    component = 'lightweight'

    def gen_yml(self, yml_parent, data):
        yml_parent.append(['lightweight-checkout', get_bool(data.text)])
