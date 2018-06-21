# encoding=utf8
import argparse
from argparse import ArgumentDefaultsHelpFormatter
import errno
import logging
import jenkins
import os
import sys
import textwrap
from jenkins_job_wrecker.modules.handlers import Handlers
from jenkins_job_wrecker.modules.listview import Listview
from jenkins_job_wrecker.registry import Registry
from jenkins_job_wrecker.helpers import gen_raw
import xml.etree.ElementTree as ET
import yaml

PY2 = sys.version_info[0] == 2
if PY2:
    reload(sys)
    sys.setdefaultencoding('utf8')

    text_type = unicode
else:
    text_type = str

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('jjwrecker')


def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        # The dumper will not respect "style='|'" if it detects trailing
        # whitespace on any line within the data. For scripts the trailing
        # whitespace is not important.
        lines = [l.strip() for l in data.splitlines()]
        data = '\n'.join(lines)
        return dumper.represent_scalar('tag:yaml.org,2002:str', data,
                                       style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_presenter)
if PY2:
    yaml.add_representer(unicode, str_presenter)



# Given a file with XML, or a string of XML, parse it with
# xml.etree.ElementTree and return the XML tree root.
def get_xml_root(filename=False, string=False):
    if not filename and not string:
        raise TypeError('specify a filename or string argument')
    if filename:
        tree = ET.parse(filename)
        return tree.getroot()
    if string:
        return ET.fromstring(string)


# Walk an XML ElementTree ("root"), and return a YAML string
def root_to_yaml(root, name, ignore_actions=False):
    # Top-level "job" data
    job = {}
    job['name'] = text_type(name)
    build = []

    # Create register
    reg = Registry()

    # "project-type:" YAML
    project_types = reg.get_project_types()

    if root.tag in project_types:
        job['project-type'] = project_types[root.tag]

        if job['project-type'] == 'pipeline':
            # For pipeline jobs, they have the
            # DisableConcurrentBuildsJobProperty tag for not allowing
            # concurrent builds, but no tag for true. JJB defaults to false,
            # this is to make it true in the event that the tag doesn't exist
            if not root.find('properties.DisableConcurrentBuildsJobProperty'):
                conElement = ET.SubElement(root, 'concurrentBuild')
                conElement.text = 'true'

        # Handle each top-level XML element with custom modules/functions in
        # modules/handlers.py
        # registry determines difference at runtime
        if job['project-type'] == 'listview':
            build.append({'view': job})
            reg = Registry(ignore_actions=ignore_actions)
            viewhandler = Listview(reg)
            viewhandler.gen_yml(job, root)
        elif job['project-type'] != 'folder':
            build.append({'job': job})
            reg = Registry(ignore_actions=ignore_actions)
            handlers = Handlers(reg)
            handlers.gen_yml(job, root)
    else:
        # Project type not currently supported, so output as raw XML
        if 'maven' in root.tag:
            job['project-type'] = 'maven'

        raw = {}
        raw['xml'] = ET.tostring(root)
        job['xml'] = {'raw': raw}

    return yaml.dump(build, default_flow_style=False, default_style=None)


# argparse foo
def parse_args(args):
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
    parser.add_argument(
        '-s', '--jenkins-server',
        help='Jenkins server to query'
    )
    parser.add_argument(
        '-n', '--name',
        help='Name of a job'
    )
    parser.add_argument(
        '-u', '--view',
        help='Name of a view'
    )
    parser.add_argument(
        '-i', '--ignore',
        nargs='*',
        help='Ignore some jobs in conversion.'
    )
    parser.add_argument(
        '-o', '--output-dir',
        default='output',
        help='folder to store generated job definitions'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true', default=None,
        help='show more output on the console'
    )
    parser.add_argument(
        '-a', '--ignore-actions-tag',
        action='store_true', default=False,
        help="will ignore the action tag values if there are any. Continues"
             " past NotImplementedError exception for <actions> tags"
    )
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])

    if args.verbose:
        log.setLevel(logging.DEBUG)

    # Options:
    # -f and -n
    # -s and -n/-u
    # -s (without -n means "all jobs on the server")
    # Choose either -f or -s ...
    if not args.jenkins_server and not args.filename:
        log.critical('Choose an XML file (-f) or Jenkins URL (-s).')
        exit(1)

    # ... but not both -f and -s.
    if args.jenkins_server and args.filename:
        log.critical('Choose either an XML file (-f) or Jenkins URL (-s).')
        exit(1)

    # -f requires -n
    if args.filename and not args.name and not args.view:
        log.critical('Choose a job name (-n) or a view name (-u) for the job'
                     ' in this file.')
        exit(1)

    # Args are ok. Proceed with writing output
    try:
        os.mkdir(args.output_dir)
    # We don't care if "output" dir already exists.
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    if args.filename:
        # Convert to YAML
        root = get_xml_root(filename=args.filename)
        yaml = root_to_yaml(root, args.name, args.ignore_actions_tag)
        # Create output directory structure where needed
        yaml_filename = os.path.join(args.output_dir, args.name + '.yml')
        path = os.path.dirname(yaml_filename)
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
        # Write to output file
        output_file = open(yaml_filename, 'w')
        output_file.write(yaml)
        output_file.close()

    # -s requires -n
    if args.jenkins_server:
        # 'http://jenkins-calamari.front.sepia.ceph.com:8080'
        # TODO: make these configurable. Allow environment variables for now
        username = None
        password = None
        try:
            username = os.environ['JJW_USERNAME']
            password = os.environ['JJW_PASSWORD']
        except KeyError as err:
            log.warning('%s was not set as an environment variable to '
                        'connect to Jenkins' % err)

        server = jenkins.Jenkins(args.jenkins_server,
                                 username=username,
                                 password=password)

        if args.name:
            job_names = [args.name]
        elif not args.view:
            job_names = []
            # Folder depth of None means go down indefinitely
            for job in server.get_jobs(folder_depth=None):
                if args.ignore and job['name'] in args.ignore:
                    log.info('Ignoring \"%s\" as requested...' % job['name'])
                    continue

                job_names.append(job['fullname'])
        else:
            job_names = []

        if args.view:
            view_names = [args.view]
        elif not args.name:
            view_names = []
            for view in server.get_views():
                if args.ignore and view['name'] in args.ignore:
                    log.info('Ignoring \"%s\" as requested...' % view['name'])
                    continue

                if view['name'] != 'all':
                    view_names.append(view['name'])
        else:
            view_names = []

        def convert_to_yml(job_names, element_type, output_dir='output'):
            """
            Takes a list of job or view names and converts them all to YAML and
            writes them to a file.

            :param list[str] job_names: Either job names or view names to get
                configs for from the server.
            :param str element_type: The type of job_names. Either 'job' or
                'view' currently.
            :param str output_dir: The directory to write the files to.
            """
            for fullname in job_names:
                log.info('looking up %s "%s"' % (element_type, fullname))
                # Get a job's XML
                if element_type == 'job':
                    xml = server.get_job_config(fullname)
                elif element_type == 'view':
                    xml = server.get_view_config(fullname)
                else:
                    log.critical('Invalid element_type.')
                    exit(1)
                log.debug(xml)
                # Convert XML to YAML
                root = get_xml_root(string=xml)
                log.info('converting %s "%s"' % (element_type, fullname))
                yaml = root_to_yaml(root, fullname, args.ignore_actions_tag)
                # Create output directory structure where needed
                yaml_filename = os.path.join(output_dir, fullname + '.yml')
                path = os.path.dirname(yaml_filename)
                try:
                    os.makedirs(path)
                except OSError as exc:  # Python >2.5
                    if exc.errno == errno.EEXIST and os.path.isdir(path):
                        pass
                    else:
                        raise
                # Write to output file
                output_file = open(yaml_filename, 'w')
                output_file.write(yaml)
                output_file.close()

        convert_to_yml(job_names, 'job')
        convert_to_yml(view_names, 'view', output_dir='output/views')
