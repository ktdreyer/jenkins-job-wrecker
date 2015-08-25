from jenkins_job_wrecker.cli import parse_args, get_xml_root
import os
import xml.etree.ElementTree
import pytest

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')

ice_setup_xml_file = os.path.join(fixtures_path, 'ice-setup.xml')

class TestArgParser(object):
    def test_missing_filename(self):
        with pytest.raises(SystemExit):
            parser = parse_args(['-f'])

    def test_ice_setup(self):
        assert parse_args(['-f', ice_setup_xml_file])


class TestGetXmlRoot(object):
    def test_missing_arg(self):
        with pytest.raises(TypeError):
            get_xml_root()

    def test_xml_root(self):
        root = get_xml_root(ice_setup_xml_file)
        assert isinstance(root, xml.etree.ElementTree.Element)
