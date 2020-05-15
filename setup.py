from __future__ import print_function
import re
import subprocess
import sys
from setuptools import setup, find_packages, Command
try:
    # Python 2 backwards compat
    from __builtin__ import raw_input as input
except ImportError:
    pass


def read_module_contents():
    with open('jenkins_job_wrecker/__init__.py') as init:
        return init.read()


module_file = read_module_contents()
metadata = dict(re.findall(r"__([a-z]+)__\s*=\s*'([^']+)'", module_file))
version = metadata['version']


class BumpCommand(Command):
    """ Bump the __version__ number and commit all changes. """

    user_options = [('version=', 'v', 'version number to use')]

    def initialize_options(self):
        new_version = metadata['version'].split('.')
        new_version[-1] = str(int(new_version[-1]) + 1)  # Bump the final part
        self.version = ".".join(new_version)

    def finalize_options(self):
        pass

    def run(self):

        print('old version: %s  new version: %s' %
              (metadata['version'], self.version))
        try:
            input('Press enter to confirm, or ctrl-c to exit >')
        except KeyboardInterrupt:
            raise SystemExit("\nNot proceeding")

        old = "__version__ = '%s'" % metadata['version']
        new = "__version__ = '%s'" % self.version
        module_file = read_module_contents()
        with open('jenkins_job_wrecker/__init__.py', 'w') as fileh:
            fileh.write(module_file.replace(old, new))

        old = 'Version:        %s' % metadata['version']
        new = 'Version:        %s' % self.version

        # Commit everything with a standard commit message
        cmd = ['git', 'commit', '-a', '-m', 'version %s' % self.version]
        print(' '.join(cmd))
        subprocess.check_call(cmd)


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
      cmdclass={
          'bump': BumpCommand,
          'release': ReleaseCommand,
      },
     )
