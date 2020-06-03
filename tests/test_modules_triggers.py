# -*- coding: utf-8 -*-
from jenkins_job_wrecker.cli import get_xml_root, root_to_yaml
import os

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'triggers')


class TestGerritTrigger(object):
    def test_gerrit_trigger_comparison(self):
        test_filename = os.path.join(fixtures_path, 'gerrit_trigger.xml')
        expected_yml_filename = os.path.join(fixtures_path, 'gerrit_trigger.yml')
        root = get_xml_root(filename=test_filename)
        actual_yml = root_to_yaml(root, "gerrit-trigger")

        with open(expected_yml_filename) as f:
            expected_yml = f.read()

        assert actual_yml is not None
        assert actual_yml == expected_yml
