.. highlight:: shell

=============
Configuration
=============

Requirements
------------

CumulusCI
=========

`metaci` is built on top of CumulusCI.  In order to use the MetaCI CLI, you should have already gone through the `CumulusCI Installation Instructions`_ to configure CumulusCI locally.

.. _CumulusCI Installation Instructions: http://cumulusci.readthedocs.io/en/latest/tutorial.html#part-1-installing-cumulusci

Salesforce DX
=============

You should have `sfdx` installed locally and connected to a defaultdevhub via JWT authentication.  To deploy a MetaCI site, you will need to provide the Client ID and JWT Private Key to authenticate with your devhub.
