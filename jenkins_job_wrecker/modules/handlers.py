import jenkins_job_wrecker.modules.base


class Handlers(jenkins_job_wrecker.modules.base.Base):
    component = 'handlers'

    def gen_yml(self, yml_parent, data):
        for child in data:
            handler_name = child.tag.lower()
            settings = []
            try:
                self.registry.dispatch(self.component, handler_name, child, settings)
                if not settings:
                    continue
                for setting in settings:
                    key, value = setting
                    if key in yml_parent:
                        yml_parent[key].append(value[0])
                    else:
                        yml_parent[key] = value
            except Exception:
                print 'last called %s' % handler_name
                raise


# Handle "<actions/>"
def actions(top, parent):
    # Nothing to do if it's empty.
    # Otherwise...
    if list(top) and len(list(top)) > 0:
        raise NotImplementedError("Don't know how to handle a "
                                  "non-empty <actions> element.")


# Handle "<authToken>tokenvalue</authToken>"
def authtoken(top, parent):
    parent.append(['auth-token', top.text])


# Handle "<description>my cool job</description>"
def description(top, parent):
    parent.append(['description', top.text])


# Handle "<keepDependencies>false</keepDependencies>"
def keepdependencies(top, parent):
    # JJB cannot handle any other value than false, here.
    # There is no corresponding YAML option.
    pass


# Handle "<canRoam>true</canRoam>"
def canroam(top, parent):
    # JJB doesn't have an explicit YAML setting for this; instead, it
    # infers it from the "node" parameter. So there's no need to handle the
    # XML here.
    pass


# Handle "<disabled>false</disabled>"
def disabled(top, parent):
    parent.append(['disabled', top.text == 'true'])


# Handle "<blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>" NOQA
def blockbuildwhendownstreambuilding(top, parent):
    parent.append(['block-downstream', top.text == 'true'])


# Handle "<blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>" NOQA
def blockbuildwhenupstreambuilding(top, parent):
    parent.append(['block-upstream', top.text == 'true'])


def concurrentbuild(top, parent):
    parent.append(['concurrent', top.text == 'true'])


def axes(top, parent):
    axes = []
    mapper = {
        'hudson.matrix.LabelExpAxis': 'label-expression',
        'hudson.matrix.LabelAxis': 'slave',
        'hudson.matrix.TextAxis': 'user-defined',
        'jenkins.plugins.shiningpanda.matrix.PythonAxis': 'python',}
    for child in top:
        try:
            axis = {'type': mapper[child.tag]}
        except KeyError:
            raise NotImplementedError("cannot handle XML %s" % child.tag)
        for axis_element in child:
            if axis_element.tag == 'name':
                axis['name'] = axis_element.text
            if axis_element.tag == 'values':
                values = []
                for value_element in axis_element:
                    values.append(value_element.text)
                axis['values'] = values
        axes.append({'axis': axis})

    parent.append(['axes', axes])


def executionstrategy(top, parent):
    strategy = {}
    for child in top:

        if child.tag == 'runSequentially':
            strategy['run-sequentially'] = (child.text == 'true')
        elif child.tag == 'sorter':
            # Is there anything but NOOP?
            pass
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    parent.append(['execution-strategy', strategy])


# Handle "<logrotator>...</logrotator>"'
def logrotator(top, parent):
    logrotate = {}
    for child in top:

        if child.tag == 'daysToKeep':
            logrotate['daysToKeep'] = child.text
        elif child.tag == 'numToKeep':
            logrotate['numToKeep'] = child.text
        elif child.tag == 'artifactDaysToKeep':
            logrotate['artifactDaysToKeep'] = child.text
        elif child.tag == 'artifactNumToKeep':
            logrotate['artifactNumToKeep'] = child.text
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    parent.append(['logrotate', logrotate])


# Handle "<combinationFilter>a != &quot;b&quot;</combinationFilter>"
def combinationfilter(top, parent):
    parent.append(['combination-filter', top.text])


# Handle "<assignedNode>server.example.com</assignedNode>"
def assignednode(top, parent):
    parent.append(['node', top.text])


# Handle "<displayName>my cool job</displayName>"
def displayname(top, parent):
    parent.append(['display-name', top.text])


# Handle "<quietPeriod>5</quietPeriod>"
def quietperiod(top, parent):
    parent.append(['quiet-period', top.text])


# Handle "<scmCheckoutRetryCount>8</scmCheckoutRetryCount>"
def scmcheckoutretrycount(top, parent):
    parent.append(['retry-count', top.text])


def customworkspace(top, parent):
    parent.append(['workspace', top.text])

def jdk(top, parent):
    parent.append(['jdk',top.text])
