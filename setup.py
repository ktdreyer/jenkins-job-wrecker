import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

version = '1.0.5'

class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main('tests', self.pytest_args)
        sys.exit(errno)

setup(name="jenkins-job-wrecker",
      version=version,
      description=('convert Jenkins XML to YAML'),
      classifiers=['Development Status :: 4 - Beta',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   ],
      keywords='jenkins xml yaml',
      author='ken dreyer',
      author_email='kdreyer [at] redhat [dot] com',
      url='https://github.com/ktdreyer/jenkins-job-wrecker',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'pyyaml',
          'python-jenkins',
      ],
      entry_points = {
        'console_scripts': [
            'jjwrecker = jenkins_job_wrecker.cli:main',
            ],
      },
      tests_require=[
          'pytest',
          'jenkins-job-builder',
     ],
      cmdclass = {'test': PyTest},
)
