from jenkins_job_wrecker.cli import parse_args, get_xml_root
import os
import xml.etree.ElementTree
import pytest

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')

ice_setup_xml_file = os.path.join(fixtures_path, 'ice-setup.xml')

class TestArgParser(object):
    
    # "-f" tests

    def test_missing_filename(self):
        with pytest.raises(SystemExit):
            parse_args(['-f'])

    def test_missing_job_name(self):
        with pytest.raises(SystemExit):
            parse_args(['-f', ice_setup_xml_file, '-n'])

    def test_ice_setup(self):
        assert parse_args(['-f', ice_setup_xml_file, '-n', 'ice-setup'])

    # "-s" tests

    def test_missing_jenkins_server(self):
        with pytest.raises(SystemExit):
            parse_args(['-s'])

    def test_jenkins_server(self):
        assert parse_args(['-s', 'http://localhost:8080'])


class TestGetXmlRoot(object):
    def test_missing_arg(self):
        with pytest.raises(TypeError):
            get_xml_root()

    def test_xml_root_with_file(self):
        root = get_xml_root(filename=ice_setup_xml_file)
        assert isinstance(root, xml.etree.ElementTree.Element)

    def test_xml_root_with_string(self):
        root = get_xml_root(string='<testing></testing>')
        assert isinstance(root, xml.etree.ElementTree.Element)
