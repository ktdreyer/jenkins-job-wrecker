# -*- coding: utf-8 -*-
from jenkins_job_wrecker.cli import get_xml_root, root_to_yaml
from jenkins_job_wrecker.modules.handlers import childcustomworkspace
import os
import yaml

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'handlers')


class TestChildCustomWorkspace(object):
    def test_basic(self):
        filename = os.path.join(fixtures_path, 'child-custom-workspace.xml')
        root = get_xml_root(filename=filename)
        assert root is not None
        parent = []
        childcustomworkspace(root, parent)
        assert len(parent) == 1
        assert parent[0][0] == "child-workspace"
        assert parent[0][1] == "lorem"

class TestCombinationFilter(object):
    def test_basic(self):
        filename = os.path.join(fixtures_path, 'combination-filter.xml')
        root = get_xml_root(filename=filename)
        jobname = "test"
        yml = root_to_yaml(root, jobname)
        dct = yaml.safe_load(yml)
        assert len(dct) == 1
        assert dct[0]['job']['execution-strategy']['combination-filter'] == "(lorem == ipsum)"