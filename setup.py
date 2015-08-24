from setuptools import setup, find_packages

version = '0.0.1'

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
      ],
      entry_points = {
        'console_scripts': [
            'jjwrecker = jenkins_job_wrecker.cli:main',
            ],
      },
)
