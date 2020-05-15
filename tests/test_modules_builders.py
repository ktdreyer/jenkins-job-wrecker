# -*- coding: utf-8 -*-
from jenkins_job_wrecker.cli import get_xml_root
from jenkins_job_wrecker.modules.builders import buildnameupdater
import os

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'builders')


class TestBuildNameSetter(object):
    def test_basic(self):
        filename = os.path.join(fixtures_path, 'build-name-setter.xml')
        root = get_xml_root(filename=filename)
        assert root is not None
        parent = []
        buildnameupdater(root, parent)
        assert len(parent) == 1
        assert 'build-name-setter' in parent[0]
        build_name_setter = parent[0]["build-name-setter"]
        assert len(build_name_setter) == 5
        assert build_name_setter["file"] == False
        assert build_name_setter["macro"] == True
        assert build_name_setter["macro-first"] == False
        assert build_name_setter["name"] == "version.txt"
        template_expected = '#${BUILD_NUMBER}-${FILE,path="BUILD_NAMER"}'
        assert build_name_setter["template"] == template_expected
