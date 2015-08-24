from jenkins_job_wrecker.cli import get_xml_root
import pytest

class TestJob(object):
    def test_missing_file(self):
        with pytest.raises(TypeError):
            result = get_xml_root()

    #def test_ice_setup(self):
    #    assert result == get_xml_root('ice-setup.xml')

# TODO: test root_to_yaml(root)
