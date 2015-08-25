Jenkins Job Wrecker
-------------------

.. image:: https://travis-ci.org/ktdreyer/jenkins-job-wrecker.svg?branch=master
       :target: https://travis-ci.org/ktdreyer/jenkins-job-wrecker

Translate Jenkins XML jobs to YAML. The YAML can then be fed into Jenkins Job
Builder.

Have a lot of Jenkins jobs that were crafted by hand over the years? This tool
allows you to convert your Jenkins jobs to JJB quickly and accurately.

Installing
----------

The module is not yet on pypi, so just install it directly from GitHub::

     virtualenv venv
     git clone https://github.com/ktdreyer/jenkins-job-wrecker.git
     python setup.py develop

You will now have a ``jjwrecker`` utility in your ``$PATH``.

Usage
-----

Let's say you have an XML definition for "my-job". Here's how you convert that
to YAML::

     jjwrecker -f path/to/my-job/config.xml -n 'my-job' | tee my-job.yaml

You can then commit ``my-job.yaml`` into your source control and use JJB to
manage the Jenkins job onward.


License
-------
MIT (see ``LICENSE``)

Copyright (c) 2015 Red Hat, Inc.
