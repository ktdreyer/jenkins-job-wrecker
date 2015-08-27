from jenkins_job_wrecker.cli import get_xml_root, root_to_yaml
import os
import pytest
import tempfile
#import jenkins_jobs.cmd
from subprocess import call

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')

class TestJJB(object):

    def run_jjb(self, name):
        filename = os.path.join(fixtures_path, name + '.xml')
        root = get_xml_root(filename=filename)
        yaml = root_to_yaml(root, name)

        # Run this wrecker YAML thru JJB.
	# XXX: shelling out with call() sucks; use JJB's API instead
        temp = tempfile.NamedTemporaryFile()
        temp.write(yaml)
        temp.flush()
        assert call(["jenkins-jobs", 'test', temp.name]) == 0
        temp.close()

    def test_ice_setup(self):
        self.run_jjb('ice-setup')

    def test_calamari_clients(self):
        self.run_jjb('calamari-clients')
