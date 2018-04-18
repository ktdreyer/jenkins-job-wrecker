# encoding=utf8
import jenkins_job_wrecker.modules.base
from jenkins_job_wrecker.helpers import get_bool


class Listview(jenkins_job_wrecker.modules.base.Base):
    component = 'listview'

    COLUMN_DICT = {
        'hudson.views.StatusColumn': 'status',
        'hudson.views.WeatherColumn': 'weather',
        'hudson.views.JobColumn': 'job',
        'hudson.views.LastSuccessColumn': 'last-success',
        'hudson.views.LastFailureColumn': 'last-failure',
        'hudson.views.LastDurationColumn': 'last-duration',
        'hudson.views.BuildButtonColumn': 'build-button',
        'hudson.views.LastStableColumn': 'last-stable',
        'hudson.plugins.robot.view.RobotListViewColum': 'robot-list',
        'hudson.plugins.findbugs.FindBugsColumn': 'find-bugs',
        'hudson.plugins.jacococoveragecolumn.JaCoCoColumn': 'jacoco',
        'hudson.plugins.git.GitBranchSpecifierColumn': 'git-branch',
        'org.jenkinsci.plugins.schedulebuild.ScheduleBuildButtonColumn': 'schedule-build',
        'jenkins.advancedqueue.PrioritySorterJobColumn': 'priority-sorter',
        'hudson.views.BuildFilterColumn': 'build-filter',
        'jenkins.branch.DescriptionColumn': 'desc',
    }

    def gen_yml(self, yml_parent, data):
        view = {'view-type': 'list'}

        for child in data:
            if child.tag == 'name':
                continue
            elif child.tag == 'filterExecutors':
                view['filter-executors'] = get_bool(child.tag)
            elif child.tag == 'filterQueue':
                view['filter-queue'] = get_bool(child.tag)
            elif child.tag == 'jobNames':
                jobs = []
                for gchild in child:
                    if gchild.tag == 'string':
                        jobs.append(gchild.text)
                view['job-name'] = jobs
            elif child.tag == 'columns':
                columns = []
                for gchild in child:
                    if gchild.tag in self.COLUMN_DICT:
                        columns.append(self.COLUMN_DICT[gchild.tag])
                view['columns'] = columns
            elif child.tag == 'recurse':
                view['recurse'] = get_bool(child.tag)
        yml_parent.update(view)
