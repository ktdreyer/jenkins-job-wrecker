Jenkins Job Wrecker
-------------------

.. image:: https://travis-ci.org/ktdreyer/jenkins-job-wrecker.svg?branch=master
       :target: https://travis-ci.org/ktdreyer/jenkins-job-wrecker

.. image:: https://badge.fury.io/py/jenkins-job-wrecker.svg
       :target: https://badge.fury.io/py/jenkins-job-wrecker

*time to get wrecked*

Translate Jenkins XML jobs to YAML. The YAML can then be fed into Jenkins Job
Builder.

Have a lot of Jenkins jobs that were crafted by hand over the years? This tool
allows you to convert your Jenkins jobs to JJB quickly and accurately.

Installing
----------

You can install a released version from PyPI::

     pip install jenkins-job-wrecker

Or, if you want to hack on it, install it directly from GitHub::

     virtualenv venv
     . venv/bin/activate
     git clone https://github.com/ktdreyer/jenkins-job-wrecker.git
     python setup.py develop

You will now have a ``jjwrecker`` utility in your ``$PATH``.

Usage
-----
Let's say you have an XML definition file for "my-job". You'll typically find
these .xml files on your Jenkins master, maybe in ``/var/lib/jenkins/jobs/``.
Here's how you convert that job file to YAML::

     jjwrecker -f path/to/my-job/config.xml -n 'my-job'

This will write ``my-job.yml`` in a directory named "``output``" in your
current working directory. You can then commit ``my-job.yml`` into your source
control and use JJB to manage the Jenkins job onward.

In addition to operating on static XML files, jjwrecker also supports querying
a live Jenkins server dynamically for a given job::

     jjwrecker -s http://jenkins.example.com/ -n 'my-job'

It will write ``output/my-job.yml`` as above.

To make jjwrecker translate every job on the server, don't specify any job
name::

     jjwrecker -s http://jenkins.example.com/

jjwrecker will iterate through all the jobs and create ``.yml`` files in
``output/``.

If your Jenkins instance requires a username and password to connect to the
remote Jenkins server, you can set these as environment variables, exported
before hand or right before running the CLI tool::

     JJW_USERNAME=alfredo JJW_PASSWORD=go-tamaulipas jjwrecker -s
     http://jenkins.ceph.com

If your Jenkins instance is using HTTPS and protected by a custom CA, add the
CA's public cert to your system certificate store:

* Fedora: ``/etc/pki/tls/certs`` directory,
* Ubuntu: ``/usr/local/share/ca-certificates/``

After you've placed the PEM-formmated file there, run ``c_reshash`` in that
directory to create the CA certificate hash symlink.  jjwrecker uses
python-jenkins, which in turn uses six's urllib, and that library will validate
HTTPS connections based on this openssl-hashed directory of certificates.


License
-------
MIT (see ``LICENSE``)

Copyright (c) 2015 Red Hat, Inc.
