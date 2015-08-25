from jenkins_job_wrecker.cli import get_xml_root, root_to_yaml
import os
import pytest
import tempfile
#import jenkins_jobs.cmd
from subprocess import call

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
ice_setup_xml_file = os.path.join(fixtures_path, 'ice-setup.xml')

class TestJJB(object):

    def test_sanity(self):
        root = get_xml_root(filename=ice_setup_xml_file)
        yaml = root_to_yaml(root, 'ice-setup')

        # Run this wrecker YAML thru JJB.
	# XXX: shelling out with call() sucks; use JJB's API instead
        temp = tempfile.NamedTemporaryFile()
        temp.write(yaml)
        temp.flush()
        assert call(["jenkins-jobs", 'test', temp.name]) == 0
        temp.close()
