# -*- coding: utf-8 -*-
from jenkins_job_wrecker.cli import get_xml_root, root_to_yaml, setup_str_presenter
import os
import tempfile
from jenkins_jobs.cli.entry import JenkinsJobs

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')


class TestJJB(object):

    def run_jjb(self, name, jobname=None):
        filename = os.path.join(fixtures_path, name + '.xml')
        root = get_xml_root(filename=filename)
        if jobname is None:
            jobname = name
        setup_str_presenter()
        yaml = root_to_yaml(root, jobname)

        # Run this wrecker YAML thru JJB.
        with tempfile.NamedTemporaryFile('w') as temp:
            temp.write(yaml)
            temp.flush()
            jjb = JenkinsJobs(['test', temp.name])
            assert jjb.execute() is None

    def compare_jjb_output(self, name, job_name):
        test_filename = os.path.join(fixtures_path, name + '.xml')
        expected_yml_filename = os.path.join(fixtures_path, name+'.yml')
        root = get_xml_root(filename=test_filename)
        actual_yml = root_to_yaml(root, job_name)

        with open(expected_yml_filename) as f:
            expected_yml = f.read()

        assert actual_yml is not None
        assert actual_yml == expected_yml

    def test_ice_setup(self):
        self.run_jjb('ice-setup')

    def test_calamari_clients(self):
        self.run_jjb('calamari-clients')

    def test_non_ascii(self):
        self.run_jjb('non-ascii', 'テスト')

    def test_indentation_with_tabs(self):
        setup_str_presenter(True)
        self.compare_jjb_output('indentation_with_tab', 'indentation_with_tab')


    def test_indentation_without_tabs(self):
        setup_str_presenter(False)
        self.compare_jjb_output('indentation_without_tab', 'indentation_without_tab')