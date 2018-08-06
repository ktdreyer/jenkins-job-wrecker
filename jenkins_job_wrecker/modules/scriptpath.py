# encoding=utf8
import jenkins_job_wrecker.modules.base


class Scriptpath(jenkins_job_wrecker.modules.base.Base):
    component = 'scriptpath'

    def gen_yml(self, yml_parent, data):
        yml_parent.append(['script-path', data.text])
