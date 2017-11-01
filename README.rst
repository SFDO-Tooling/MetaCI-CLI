==========
MetaCI CLI
==========


.. image:: https://img.shields.io/pypi/v/metaci_cli.svg
        :target: https://pypi.python.org/pypi/metaci_cli

.. image:: https://readthedocs.org/projects/metaci-cli/badge/?version=latest
        :target: https://metaci-cli.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/jlantz/metaci_cli/shield.svg
     :target: https://pyup.io/repos/github/jlantz/metaci_cli/
     :alt: Updates


A command line interface for MetaCI, a CI app run on Heroku for Salesforce development projects


* Free software: BSD license
* Documentation: https://metaci-cli.readthedocs.io.


Features
--------

* Auto-detects and loads CumulusCI's configuration when inside a project's local git repository
* Deploy a MetaCI site to Heroku with `metaci site add`
* Connect to an existing MetaCI site with `metaci site connect`
* Interact with builds with `metaci build`
* Interact with orgs with `metaci org`
* Interact with plans with `metaci plans`
* Interact with services with `metaci services`

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
