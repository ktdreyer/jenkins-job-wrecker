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
from jenkins_job_wrecker.registry import Registry
import xml.etree.ElementTree as ET
import yaml

is_py_v2 = True if sys.version[0] == '2' else False
if is_py_v2:
    reload(sys)
    sys.setdefaultencoding('utf8')

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('jjwrecker')


def str_presenter(dumper, data):
  if len(data.splitlines()) > 1:  # check for multiline string
    # The dumper will not respect "style='|'" if it detects trailing
    # whitespace on any line within the data. For scripts the trailing
    # whitespace is not important.
    lines = [l.strip() for l in data.splitlines()]
    data = '\n'.join(lines)
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
  return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)


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
def root_to_yaml(root, name):
    # Top-level "job" data
    job = {}
    build = [{'job': job}]

    job['name'] = str(name)

    # "project-type:" YAML
    project_types = {
        'project': 'freestyle',
        'matrix-project': 'matrix'}
    if root.tag in project_types:
        job['project-type'] = project_types[root.tag]

        # Handle each top-level XML element with custom "handle_*" functions in
        # modudles/handlers.py.
        reg = Registry()
        handlers = Handlers(reg)
        handlers.gen_yml(job, root)
    else:
        # Project type not currently supported, so output as raw XML
        if 'maven' in root.tag:
            job['project-type'] = 'maven'

        raw = {}
        raw['xml'] = ET.tostring(root)
        job['xml'] = {'raw':raw}

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
        '-i', '--ignore',
        nargs='*',
        help='Ignore some jobs in conversion.'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true', default=None,
        help='show more output on the console'
    )
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])

    if args.verbose:
        log.setLevel(logging.DEBUG)

    # Options:
    # -f and -n
    # -s and -n
    # TODO: -s (without -n means "all jobs on the server")
    # Choose either -f or -s ...
    if not args.jenkins_server and not args.filename:
        log.critical('Choose an XML file (-f) or Jenkins URL (-s).')
        exit(1)

    # ... but not both -f and -s.
    if args.jenkins_server and args.filename:
        log.critical('Choose either an XML file (-f) or Jenkins URL (-s).')
        exit(1)

    # -f requires -n
    if args.filename and not args.name:
        log.critical('Choose a job name (-n) for the job in this file.')
        exit(1)

    # Args are ok. Proceed with writing output
    try:
        os.mkdir('output')
    # We don't care if "output" dir already exists.
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    if args.filename:
        # Convert to YAML
        root = get_xml_root(filename=args.filename)
        yaml = root_to_yaml(root, args.name)
        # Create output directory structure where needed
        yaml_filename = os.path.join('output', args.name + '.yml')
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
        else:
            job_names = []
            for job in server.get_jobs():

                if args.ignore and job['name'] in args.ignore:
                    log.info('Ignoring \"%s\" as requested...' % job['name'])
                    continue

                job_names.append(job['name'])

        # write YAML
        for name in job_names:
            log.info('looking up job "%s"' % name)
            # Get a job's XML
            xml = server.get_job_config(name)
            log.debug(xml)
            # Convert XML to YAML
            root = get_xml_root(string=xml)
            log.info('converting job "%s" to YAML' % name)
            yaml = root_to_yaml(root, name)
            # Create output directory structure where needed
            yaml_filename = os.path.join('output', name + '.yml')
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
