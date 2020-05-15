# -*- coding: utf-8 -*-
from jenkins_job_wrecker.cli import get_xml_root
from jenkins_job_wrecker.modules.publishers import groovypostbuildrecorder
import os

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'publishers')


class TestGroovyPostbuildPlugin(object):
    def test_v2(self):
        filename = os.path.join(fixtures_path, 'groovy-postbuild-v2.xml')
        root = get_xml_root(filename=filename)
        assert root is not None
        parent = []
        groovypostbuildrecorder(root, parent)
        assert len(parent) == 1
        assert 'groovy-postbuild' in parent[0]
        jjb_groovy_postbuild = parent[0]['groovy-postbuild']
        assert jjb_groovy_postbuild['matrix-parent'] is False
        assert jjb_groovy_postbuild['on-failure'] == 'nothing'
        assert jjb_groovy_postbuild['sandbox'] is False
        assert jjb_groovy_postbuild['script'] == 'foo bar'
