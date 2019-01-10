from __future__ import print_function
import re
import subprocess
import sys
from setuptools import setup, find_packages, Command
from setuptools.command.test import test as TestCommand


def read_module_contents():
    with open('jenkins_job_wrecker/__init__.py') as init:
        return init.read()


module_file = read_module_contents()
metadata = dict(re.findall(r"__([a-z]+)__\s*=\s*'([^']+)'", module_file))
version = metadata['version']


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
        import pytest
        errno = pytest.main('tests', self.pytest_args)
        sys.exit(errno)


class ReleaseCommand(Command):
    """ Tag and push a new release. """

    user_options = [('sign', 's', 'GPG-sign the Git tag and release files')]

    def initialize_options(self):
        self.sign = False

    def finalize_options(self):
        pass

    def run(self):
        # Create Git tag
        tag_name = 'v%s' % version
        cmd = ['git', 'tag', '-a', tag_name, '-m', 'version %s' % version]
        if self.sign:
            cmd.append('-s')
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Push Git tag to origin remote
        cmd = ['git', 'push', 'origin', tag_name]
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Push branch to origin remote
        cmd = ['git', 'push', 'origin', 'master']
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Create source package
        cmd = ['python', 'setup.py', 'sdist']
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        tarball = 'dist/%s-%s.tar.gz' % ('jenkins-job-wrecker', version)

        # GPG sign
        if self.sign:
            cmd = ['gpg2', '-b', '-a', tarball]
            print(' '.join(cmd))
            subprocess.check_call(cmd)

        # Upload
        cmd = ['twine', 'upload', tarball]
        if self.sign:
            cmd.append(tarball + '.asc')
        print(' '.join(cmd))
        subprocess.check_call(cmd)


setup(name="jenkins-job-wrecker",
      version=version,
      description=('convert Jenkins XML to YAML'),
      classifiers=['Development Status :: 4 - Beta',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Software Development :: Libraries :: Python Modules',  # NOQA
                  ],
      keywords='jenkins xml yaml',
      author='ken dreyer',
      author_email='kdreyer@redhat.com',
      url='https://github.com/ktdreyer/jenkins-job-wrecker',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'pyyaml',
          'python-jenkins',
      ],
      entry_points={
          'console_scripts': [
              'jjwrecker = jenkins_job_wrecker.cli:main',
          ],
      },
      tests_require=[
          'pytest',
          'jenkins-job-builder',
      ],
      cmdclass={
          'release': ReleaseCommand,
          'test': PyTest,
      },
     )
