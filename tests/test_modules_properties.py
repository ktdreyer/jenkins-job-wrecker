# -*- coding: utf-8 -*-
from jenkins_job_wrecker.cli import get_xml_root
from jenkins_job_wrecker.modules.properties import authorizationmatrixproperty
import os

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'properties')


class TestAuthorizationMatrixProperty(object):
    def test_basic(self):
        filename = os.path.join(fixtures_path, 'authorization-matrix-property.xml')
        root = get_xml_root(filename=filename)
        assert root is not None
        parent = []
        authorizationmatrixproperty(root, parent)
        assert len(parent) == 1
        assert 'authorization' in parent[0]
        jjb_authorization = parent[0]['authorization']
        assert len(jjb_authorization) == 2
        assert jjb_authorization['usera'] == ['job-build', 'job-read']
        assert jjb_authorization['userb'] == ['job-configure', 'job-workspace']
