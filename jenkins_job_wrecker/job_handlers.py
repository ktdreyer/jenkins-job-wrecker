# Handle "<actions/>"
def handle_actions(top):
    # Nothing to do if it's empty.
    # Otherwise...
    if list(top) and len(list(top)) > 0:
        raise NotImplementedError, "Don't know how to handle a non-empty <actions> element."


# Handle "<description>my cool job</description>"
def handle_description(top):
    return [['description', top.text]]

# Handle "<keepDependencies>false</keepDependencies>"
def handle_keepdependencies(top):
    return [['keep-dependencies', top.text == 'true']]

# Handle "<properties>..."
def handle_properties(top):
    properties = []
    parameters = []
    for child in top:
        # GitHub
        if child.tag == 'com.coravy.hudson.plugins.github.GithubProjectProperty':
            github = handle_github_project_property(child)
            properties.append(github)
        # Parameters
        elif child.tag == 'hudson.model.ParametersDefinitionProperty':
            parametersdefs = handle_parameters_property(child)
            for pd in parametersdefs:
                parameters.append(pd)
        # A property we don't know about
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)
    return [['properties', properties], ['parameters', parameters]]

# Handle "<com.coravy.hudson.plugins.github.GithubProjectProperty>..."
def handle_github_project_property(top):
    github = {}
    for child in top:
        if child.tag == 'projectUrl':
            github['url'] = child.text
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)
    return {'github': github}

# Handle "<hudson.model.ParametersDefinitionProperty>..."
def handle_parameters_property(top):
    parameters = []
    for parameterdefs in top:
        if parameterdefs.tag != 'parameterDefinitions':
            raise NotImplementedError("cannot handle XML %s" % parameterdefinitions.tag)
        for parameterdef in parameterdefs:
            if parameterdef.tag == 'hudson.model.StringParameterDefinition':
                parameter_type = 'string'
            elif parameterdef.tag == 'hudson.model.BooleanParameterDefinition':
                parameter_type = 'bool'
            else:
                raise NotImplementedError(parameterdefinition.tag)

            parameter_settings = {}
            for defsetting in parameterdef:
                key = {
                    'defaultValue': 'default',
                }.get(defsetting.tag, defsetting.tag)
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
                # Assume that PyYAML will handle everything else correctly 
                else:
                   value = defsetting.text
                parameter_settings[key] = value
            parameters.append({parameter_type: parameter_settings})
    return parameters

# Handle "<scm>..."
def handle_scm(top):
    # TODO: ensure that this is a hudson.plugins.git.GitSCM
    git = {}
    for child in top:

        if child.tag == 'configVersion':
            continue # we don't care

        elif child.tag == 'userRemoteConfigs':
            if len(list(child)) != 1:
               # expected "hudson.plugins.git.UserRemoteConfig" tag
               raise NotImplementedError("%s not supported with %i children" % (child.tag, len(list(child)) ))
            if len(list(child[0])) != 1:
               # expected "url" tag
               raise NotImplementedError("%s not supported with %i children" % (child.tag, len(list(child)) ))
            if child[0][0].tag != 'url':
               raise NotImplementedError("%s XML not supported" % child[0][0].tag)
            git['url'] = child[0][0].text

        elif child.tag == 'branches':
            if len(list(child)) != 1:
               # expected hudson.plugins.git.BranchSpec
               raise NotImplementedError("%s not supported with %i children" % (child.tag, len(list(child)) ))
            if len(list(child[0])) != 1:
               # expected name
               raise NotImplementedError("%s not supported with %i children" % (child[0].tag, len(list(child[0])) ))
            if child[0][0].tag != 'name':
               raise NotImplementedError("%s XML not supported" % child[0][0].tag)
            git['branches'] = child[0][0].text

        elif child.tag == 'doGenerateSubmoduleConfigurations':
            if len(list(child)) != 0:
               raise NotImplementedError("%s not supported with %i children" % (child.tag, len(list(child)) ))
            # JJB doesn't handle this element anyway. Just continue on.
            continue

        elif child.tag == 'submoduleCfg':
            if len(list(child)) > 0:
               raise NotImplementedError("%s not supported with %i children" % (child.tag, len(list(child)) ))

        elif child.tag == 'extensions':
            if len(list(child)) != 1:
               # hudson.plugins.git.extensions.impl.RelativeTargetDirectory
               raise NotImplementedError("%s not supported with %i children" % (child.tag, len(list(child)) ))
            if len(list(child[0])) != 1:
               # expected relativeTargetDir
               raise NotImplementedError("%s not supported with %i children" % (child[0].tag, len(list(child[0])) ))
            if child[0][0].tag != 'relativeTargetDir':
               raise NotImplementedError("%s XML not supported" % child[0][0].tag)
            git['basedir'] = child[0][0].text

        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)
    return [[ 'scm', [{'git': git}] ]]

# Handle "<canRoam>true</canRoam>"
def handle_canroam(top):
    # JJB doesn't have an explicit YAML setting for this; instead, it
    # infers it from the "node" parameter. So there's no need to handle the
    # XML here.
    return None

# Handle "<disabled>false</disabled>"
def handle_disabled(top):
    return [['disabled', top.text == 'true']]

# Handle "<blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>"
def handle_blockbuildwhendownstreambuilding(top):
    return [['block-downstream', top.text == 'true']]

# Handle "<blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>"
def handle_blockbuildwhenupstreambuilding(top):
    return [['block-upstream', top.text == 'true']]
    
def handle_triggers(top):
    if len(list(top)) > 0:
       raise NotImplementedError('TODO: implement handling here')

def handle_concurrentbuild(top):
    return [['concurrent', top.text == 'true']]

def handle_axes(top):
    axes = []
    for child in top:

        if child.tag == 'hudson.matrix.LabelExpAxis':
            axis = {'type': 'label-expression'}
            for axis_element in child:
                if axis_element.tag == 'name':
                    axis['name'] = axis_element.text
                if axis_element.tag == 'values':
                    values = []
                    for value_element in axis_element:
                       values.append(value_element.text)
                    axis['values'] = values
            axes.append({'axis': axis})

        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    return [[ 'axes', axes ]]

def handle_builders(top):
    builders = []
    for child in top:

        if child.tag == 'hudson.tasks.Shell':
            for shell_element in child:
                # Assumption: there's only one <command> in this
                # <hudson.tasks.Shell>
                if shell_element.tag == 'command':
                    shell = shell_element.text
                else:
                    raise NotImplementedError("cannot handle XML %s" % shell_element.tag)
            builders.append({'shell': shell})

        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    return [[ 'builders', builders ]]

def handle_publishers(top):
    publishers = []
    for child in top:

        if child.tag == 'hudson.tasks.ArtifactArchiver':
            archive = {}
            for element in child:
                if element.tag == 'artifacts':
                    archive['artifacts'] = element.text
                elif element.tag == 'allowEmptyArchive':
                    archive['allow-empty'] = (element.text == 'true')
                elif element.tag == 'fingerprint':
                    archive['fingerprint'] = (element.text == 'true')
                elif element.tag == 'onlyIfSuccessful':
                    # only-if-success is not yet available in JJB 1.2.0
                    archive['only-if-success'] = (element.text == 'true')
                elif element.tag == 'defaultExcludes':
                    # default-excludes is not yet available in JJB master
                    archive['default-excludes'] = (element.text == 'true')
                else:
                    raise NotImplementedError("cannot handle XML %s" % element.tag)

            publishers.append({'archive': archive})

        elif child.tag == 'hudson.plugins.descriptionsetter.DescriptionSetterPublisher':
            setter = {}
            for element in child:
                if element.tag == 'regexp':
                    setter['regexp'] = element.text
                elif element.tag == 'regexpForFailed':
                    setter['regexp-for-failed'] = element.text
                elif element.tag == 'setForMatrix':
                    setter['set-for-matrix'] = (element.text == 'true')
                else:
                    raise NotImplementedError("cannot handle XML %s" % element.tag)

            publishers.append({'description-setter': setter})

        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    return [[ 'publishers', publishers ]]

def handle_buildwrappers(top):
    wrappers = []
    for child in top:

        if child.tag == 'EnvInjectPasswordWrapper':
            inject = {}
            for element in child:
                if element.tag == 'injectGlobalPasswords':
                    inject['global'] = (element.text == 'true')
                elif element.tag == 'maskPasswordParameters':
                    inject['mask-password-params'] = (element.text == 'true')
                elif element.tag == 'passwordEntries':
                    if len(list(element)) > 0:
                       raise NotImplementedError('TODO: implement handling here')
                else:
                    raise NotImplementedError("cannot handle XML %s" % element.tag)
            wrappers.append({'inject': inject})
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)
    return [[ 'wrappers', wrappers ]]

def handle_executionstrategy(top):
    strategy = {}
    for child in top:

        if child.tag == 'runSequentially':
            strategy['run-sequentially'] = (child.text == 'true')
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    return [[ 'execution-strategy', strategy ]]


def parse_args():
    parser = argparse.ArgumentParser(
        description='Input XML, output YAML.',
        epilog=textwrap.dedent('''
        Examples:
        jjwrecker -f ice-tools.xml
        '''),
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-f', '--filename',
        help='XML file to translate'
    )
    return parser.parse_args()

def main():
    global args
    args = parse_args()

    if not args.filename:
        log.critical('XML Filename (-f) must be set. Exiting...')
        exit(1)

    root = get_root(args.filename)
    print print_job(root)

# Given an XML filename, parse it with xml.etree.ElementTree and return the XML
# tree root.
def get_root(filename):
    tree = ET.parse(filename)
    return tree.getroot()
