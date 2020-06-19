# -*- coding: utf-8 -*-
from jenkins_job_wrecker.cli import get_xml_root
from jenkins_job_wrecker.modules.buildwrappers import prebuildcleanup
import os

fixtures_path = os.path.join(os.path.dirname(
    __file__), 'fixtures', 'buildwrappers')


class TestPreBuildCleanup(object):
    def test_basic(self):
        filename = os.path.join(fixtures_path, 'prebuildcleanup.xml')
        root = get_xml_root(filename=filename)
        assert root is not None
        parent = []
        prebuildcleanup(root, parent)
        assert len(parent) == 1
        assert 'workspace-cleanup' in parent[0]
        jjb_ws_cleanup = parent[0]['workspace-cleanup']
        assert jjb_ws_cleanup['dirmatch'] is True
        assert jjb_ws_cleanup['disable-deferred-wipeout'] is True
        assert jjb_ws_cleanup['check-parameter'] == 'DO_WS_CLEANUP'
        assert jjb_ws_cleanup['external-deletion-command'] == 'shred -u %s'

    def test_empty_value(self):
        filename = os.path.join(fixtures_path, 'prebuildcleanup_empty_value.xml')
        root = get_xml_root(filename=filename)
        assert root is not None
        parent = []
        prebuildcleanup(root, parent)
        assert len(parent) == 1
        assert 'workspace-cleanup' in parent[0]
        jjb_ws_cleanup = parent[0]['workspace-cleanup']
        assert jjb_ws_cleanup['dirmatch'] is True
        assert jjb_ws_cleanup['disable-deferred-wipeout'] is True
        assert 'external-deletion-command' not in jjb_ws_cleanup
        assert 'check-parameter' not in jjb_ws_cleanup
