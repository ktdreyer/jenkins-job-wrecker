from jenkins_job_wrecker.cli import parse_args, get_xml_root
import xml.etree.ElementTree
import pytest

class TestArgParser(object):
    def test_missing_filename(self):
        with pytest.raises(SystemExit):
            parser = parse_args(['-f'])

    def test_ice_setup(self):
        assert parse_args(['-f', 'ice-setup.xml'])


class TestGetXmlRoot(object):
    def test_missing_arg(self):
        with pytest.raises(TypeError):
            get_xml_root()

    def test_xml_root(self):
        root = get_xml_root('ice-setup.xml')
        assert isinstance(root, xml.etree.ElementTree.Element)
