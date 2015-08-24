import argparse
from argparse import ArgumentDefaultsHelpFormatter
import logging
import textwrap
import jenkins_job_wrecker.job_handlers as job_handlers
import xml.etree.ElementTree as ET
from yaml import dump

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('jjwrecker')

# set the format of the standard StreamHandler to have a space in it
# (on the root logger)
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(logging.Formatter(fmt='%(name)s %(levelname)s: %(message)s'))


# Given an XML filename, parse it with xml.etree.ElementTree and return the XML
# tree root.
def get_xml_root(filename):
    tree = ET.parse(filename)
    return tree.getroot()

# Walk an XML ElementTree ("root"), and return a YAML string
def root_to_yaml(root):
    # Top-level "job" data
    job = {}
    build = [{'job': job}]

    if root.tag != 'matrix-project':
       raise NotImplementedError, 'We only support matrix-type jobs'

    job['project-type'] = 'matrix'

    # Handle each top-level XML element with custom "handle_*" functions in
    # job_handlers.py.
    for child in root:
        handler_name = 'handle_%s' % child.tag.lower()
        try:
            handler = getattr(job_handlers, handler_name)
        except AttributeError:
            # Show our YAML translation so far:
            print dump(build, default_flow_style=False)
            # ... and report what still needs to be done:
            raise NotImplementedError("write a function for %s" % handler_name)
        try:
            settings = handler(child)
            if settings is not None:
                for setting in settings:
                    key, value = setting
                    job[key] = value
        except Exception, e:
            print 'last called %s' % handler_name
            raise

    return dump(build, default_flow_style=False)

# argparse foo
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

    root = get_xml_root(args.filename)
    print root_to_yaml(root)
