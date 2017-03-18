# encoding=utf8
import jenkins_job_wrecker.modules.base


class Sandbox(jenkins_job_wrecker.modules.base.Base):
    component = 'sandbox'

    def gen_yml(self, yml_parent, data):
        yml_parent.append(['sandbox', data.text])

