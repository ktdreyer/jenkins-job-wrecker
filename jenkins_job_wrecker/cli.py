import argparse
from argparse import ArgumentDefaultsHelpFormatter
import errno
import logging
import jenkins
import os
import sys
import textwrap
import jenkins_job_wrecker.job_handlers as job_handlers
import xml.etree.ElementTree as ET
import yaml


logging.basicConfig(level=logging.INFO)
log = logging.getLogger('jjwrecker')

# set the format of the standard StreamHandler to have a space in it
# (on the root logger)
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(logging.Formatter(fmt='%(name)s %(levelname)s: '
                                                   '%(message)s'))


class literal_unicode(unicode): pass


def literal_unicode_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')


yaml.add_representer(literal_unicode, literal_unicode_representer)


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

    job['name'] = name

    # "project-type:" YAML
    project_types = {
        'project': 'freestyle',
        'matrix-project': 'matrix'}
    if root.tag in project_types:
        job['project-type'] = project_types[root.tag]

        # Handle each top-level XML element with custom "handle_*" functions in
        # job_handlers.py.
        for child in root:
            handler_name = 'handle_%s' % child.tag.lower()
            try:
                handler = getattr(job_handlers, handler_name)
            except AttributeError:
                # Show our YAML translation so far:
                print yaml.dump(build, default_flow_style=False)
                # ... and report what still needs to be done:
                raise NotImplementedError("write a function for %s" % handler_name)
            try:
                settings = handler(child)

                if not settings:
                    continue

                for setting in settings:
                    key, value = setting
                    if key in job:
                        job[key].append(value[0])
                    else:
                        job[key] = value
            except Exception:
                print 'last called %s' % handler_name
                raise
    else:
        # Project type not currently supported, so output as raw XML
        if 'maven' in root.tag:
            job['project-type'] = 'maven'

        raw = {}
        raw['xml'] = ET.tostring(root)
        job['xml'] = {'raw':raw}

    # any shell or script elements should be treated as literals
    def format_shell_scripts(data):
        for k, v in data.iteritems():
            if type(v) is dict:
                format_shell_scripts(v)
            elif type(v) is list:
                for lv in v:
                    if type(lv) is dict:
                        format_shell_scripts(lv)
            else:
                if k == 'shell' or k == 'script':
                    data[k] = literal_unicode(v)

    for build_element in build:
        format_shell_scripts(build_element)

    return yaml.dump(build, default_flow_style=False)


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
        # write yaml string to file (job-name.yml)
        yaml_filename = os.path.join('output', args.name + '.yml')
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

                if job['name'] in args.ignore:
                    log.info('Ignoring [%s] as requested...' % job)
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
            # write yaml string to file (job-name.yml)
            yaml_filename = os.path.join('output', name + '.yml')
            output_file = open(yaml_filename, 'w')
            output_file.write(yaml)
            output_file.close()
