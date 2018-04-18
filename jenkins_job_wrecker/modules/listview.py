# encoding=utf8
import jenkins_job_wrecker.modules.base
from jenkins_job_wrecker.helpers import get_bool, gen_raw


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
                continue  # Name already declared in other section of YAML
            elif child.tag == 'description':
                view['description'] = child.text
            elif child.tag == 'filterExecutors':
                view['filter-executors'] = get_bool(child.text)
            elif child.tag == 'filterQueue':
                view['filter-queue'] = get_bool(child.text)
            elif child.tag == 'jobFilters':
                filters = {}
                for gchild in child:
                    # most-recent filter
                    if gchild.tag == 'hudson.views.MostRecentJobsFilter':
                        recent = {}
                        filters['most-recent'] = recent
                        for ggchild in gchild:
                            if ggchild.tag == 'maxToInclude':
                                recent['max-to-include'] = int(ggchild.text)
                            elif ggchild.tag == 'checkStartTime':
                                recent['check-start-time'] = get_bool(ggchild.text)
                            else:
                                raise NotImplementedError("cannot handle XML %s" % ggchild.tag)
                    # build-duration filter
                    elif gchild.tag == 'hudson.views.BuildDurationFilter':
                        builddur = {}
                        filters['build-duration'] = builddur
                        for ggchild in gchild:
                            if ggchild.tag == 'includeExcludeTypeString':
                                builddur['match-type'] = ggchild.text
                            elif ggchild.tag == 'buildCountTypeString':
                                builddur['build-duration-type'] = ggchild.text
                            elif ggchild.tag == 'amountTypeString':
                                builddur['amount-type'] = ggchild.text
                            elif ggchild.tag == 'amount':
                                builddur['amount'] = int(ggchild.text)
                            elif ggchild.tag == 'lessThan':
                                builddur['less-than'] = get_bool(ggchild.text)
                            elif ggchild.tag == 'buildDurationMinutes':
                                builddur['build-duration-minutes'] = int(ggchild.text)
                            else:
                                raise NotImplementedError("cannot handle XML %s" % ggchild.tag)
                    # build-trend filter
                    elif gchild.tag == 'hudson.views.BuildTrendFilter':
                        trend = {}
                        filters['build-trend'] = trend
                        for ggchild in gchild:
                            if ggchild.tag == 'includeExcludeTypeString':
                                trend['match-type'] = ggchild.text
                            elif ggchild.tag == 'buildCountTypeString':
                                trend['build-trend-type'] = ggchild.text
                            elif ggchild.tag == 'amountTypeString':
                                trend['amount-type'] = ggchild.text
                            elif ggchild.tag == 'amount':
                                trend['amount'] = int(ggchild.text)
                            elif ggchild.tag == 'statusTypeString':
                                trend['status'] = ggchild.text
                            else:
                                raise NotImplementedError("cannot handle XML %s" % ggchild.tag)
                    # job-status filter
                    elif gchild.tag == 'hudson.views.JobStatusFilter':
                        status = {}
                        filters['job-status'] = status
                        for ggchild in gchild:
                            if ggchild.tag == 'includeExcludeTypeString':
                                status['match-type'] = ggchild.text
                            elif ggchild.tag == 'unstable':
                                status['unstable'] = get_bool(ggchild.text)
                            elif ggchild.tag == 'failed':
                                status['failed'] = get_bool(ggchild.text)
                            elif ggchild.tag == 'aborted':
                                status['aborted'] = get_bool(ggchild.text)
                            elif ggchild.tag == 'disabled':
                                status['disabled'] = get_bool(ggchild.text)
                            elif ggchild.tag == 'stable':
                                status['stable'] = get_bool(ggchild.text)
                            else:
                                raise NotImplementedError("cannot handle XML %s" % ggchild.tag)
                    # Need to gen raw for filters, not implemented at all
                    else:
                        filters = {}  # Empty out filters
                        raw_xml = []
                        gen_raw(child, raw_xml)
                        raw_str_xml = raw_xml[0]['raw']['xml']
                        # Needs to be ['raw']['xml'], not [0]['raw']['xml'],
                        #   as view is a dictionary
                        if 'raw' not in view:
                            view['raw'] = {'xml': raw_str_xml}
                        else:
                            view['raw']['xml'] += raw_str_xml
                        break
                # End of jobFilters loop
                if filters:
                    view['job-filters'] = filters
            # End of jobFilters
            elif child.tag == 'jobNames':
                jobs = []
                for gchild in child:
                    if gchild.tag == 'string':
                        jobs.append(gchild.text)
                if jobs:
                    view['job-name'] = jobs
            elif child.tag == 'columns':
                if len(child) == 0:
                    continue
                columns = []
                for gchild in child:
                    if gchild.tag in self.COLUMN_DICT:
                        columns.append(self.COLUMN_DICT[gchild.tag])
                view['columns'] = columns
            elif child.tag == 'recurse':
                view['recurse'] = get_bool(child.text)
            elif child.tag == 'includeRegex':
                view['regex'] = child.text
            elif child.tag == 'statusFilter':
                view['status-filter'] = get_bool(child.text)
            elif child.tag == 'properties':
                # Not sure what this tag is for, doesn't seem important
                continue
            else:
                raise NotImplementedError("cannot handle XML %s" % child.tag)
        yml_parent.update(view)
