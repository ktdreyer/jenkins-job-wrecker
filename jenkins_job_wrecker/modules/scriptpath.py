# encoding=utf8
import jenkins_job_wrecker.modules.base


class Scriptpath(jenkins_job_wrecker.modules.base.Base):
    component = 'scriptpath'

    def gen_yml(self, yml_parent, data):

        scriptPath = ""
        yml_parent.append(['scriptPath', data.text])
