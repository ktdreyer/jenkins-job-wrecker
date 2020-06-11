# -*- coding: utf-8 -*-
from jenkins_job_wrecker.cli import get_xml_root
from jenkins_job_wrecker.modules.properties import authorizationmatrixproperty, buildblockerproperty
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


class TestBuildBlockerProperty(object):
    def test_with_blocker_jobs(self):
        filename = os.path.join(fixtures_path, 'build-blocker-property-with-blocking-jobs.xml')
        root = get_xml_root(filename=filename)
        assert root is not None
        parent = []
        buildblockerproperty(root, parent)
        assert len(parent) == 1
        build_blocker = parent[0]["build-blocker"]
        assert build_blocker["use-build-blocker"]
        assert build_blocker["block-level"] == "GLOBAL"
        assert build_blocker["queue-scanning"] == "DISABLED"
        blocking_jobs = build_blocker["blocking-jobs"]
        assert len(blocking_jobs) == 3
        assert blocking_jobs[0] == "test"
        assert blocking_jobs[1] == "test2"
        assert blocking_jobs[2] == "test 3"

    def test_without_blocker_jobs(self):
        filename = os.path.join(fixtures_path, 'build-blocker-property-without-blocking-jobs.xml')
        root = get_xml_root(filename=filename)
        assert root is not None
        parent = []
        buildblockerproperty(root, parent)
        assert len(parent) == 1
        build_blocker = parent[0]["build-blocker"]
        assert not build_blocker["use-build-blocker"]
        assert build_blocker["block-level"] == "GLOBAL"
        assert build_blocker["queue-scanning"] == "DISABLED"
        blocking_jobs = build_blocker["blocking-jobs"]
        assert len(blocking_jobs) == 0
