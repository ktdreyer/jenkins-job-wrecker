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
Let's say you have an XML definition file for "my-job". Here's how you convert
that to YAML::

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

It is required to determine a username and password to connect to the remote
Jenkins server. These credentials can be set as normal environment variables,
exported before hand or right before running the CLI tool::

     JJW_USERNAME=alfredo JJW_PASSWORD=go-tamaulipas jjwrecker -s
     http://jenkins.ceph.com


License
-------
MIT (see ``LICENSE``)

Copyright (c) 2015 Red Hat, Inc.
