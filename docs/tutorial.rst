.. highlight:: shell

========
Tutorial
========

Prerequirements
---------------

* Follow the Installation and Configuration sections of this document

  * Install `metaci_cli`
  * Install and configure CumulusCI
  * Install and configure Salesforce DX

Configuring the Demo Repository
-------------------------------

Fork the repository
===================

Go to https://github.com/SalesforceFoundation/MetaCI-DF17-Demo-Project and click the `Fork` button to make a fork of the repository under your Github user account.

Clone the forked repository to your local system.

Creating the Packaging Org
==========================

For this tutorial, we'll be automating the release of a managed package of our project.  To make this possible, you need a new Developer Edition org which will serve as your packaging org.  In a fresh DE org, go to Setup -> Packages and create a new Unmanaged Package named whatever you want to call your demo project package.  Then, assign a namespace and point it at the Unmanaged Package you just created.

Configure for CumulusCI
=======================

Create a feature branch to be in line with CumulusCI's feature branch model:

.. code-block:: console

    $ git checkout -b feature/cumulusci

Initialize the CumulusCI configuration for the repository.  Use the package name and namespace you used in the packaging org:

.. code-block:: console

    $ cci project init

Stage and commit the changes:

.. code-block:: console

    $ git add cumulusci.yml orgs sfdx-project.json
    $ git commit -m "Configure for CumulusCI"

For now, we'll hold off on pushing the `feature/cumulusci` branch until we get MetaCI set up to build our project.

Connect the Packaging Org
=========================

Run `cci org connect packaging` and log into the packaging org in the browser window that pops up.  Once you get the 'OK' screen you can close the browser.  Use `cci org list` to verify that the packaging org is now connected to `cci`'s project keychain.


Deploy MetaCI to Heroku
-----------------------

In this section, you will deploy a new MetaCI site on Heroku using free dyno resources.  You will need the Client ID and JWT Private Key file used to authenticate to your Salesforce DX devhub.  You will also need either the `heroku` CLI installed and authenticated or the Heroku API Token.

To launch your MetaCI site:

.. code-block:: console
    
    $ metaci site add
    MetaCI CLI v0.1.0
    
    # Heroku App Name
    Specify the name of the Heroku app you want to create.
    App Name: your-app-name-here
    
    # Heroku App Shape
    Select the Heroku app shape you want to deploy.  Available options:
      - dev: Runs on free Heroku resources with build concurrency of 1
      - staging: Runs on paid Heroku resources with fixed build concurrency of X
      - prod: Runs on paid Heroku resources auto-scaled build concurrency via Hirefire.io (paid add on configured separately)
    App Shape [dev]:
    
    # Salesforce DX Configuration
    The following prompts collect information from your local Salesforce DX configuration to use to configure MetaCI to use sfdx
    
    MetaCI uses JWT to connect to your Salesforce DX devhub.  Please enter the path to your local private key file.  If you have not set up JWT for your devhub, refer to the documentation: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_jwt_flow.htm
    Path to private key [/Users/YOUR_USERNAME/.ssh/sfdx_server.key]: 
    
    Enter the Connected App Client ID you used for the JWT authentication flow to the Salesforce DX devhub.
    NOTE: For security purposes, your input will be hidden.  Paste your Client ID and hit Enter to continue.
    Client ID:

Use the following settings:

* **App Name**: Enter a valid heroku app name such as `metaci-your-org-test`
* **App Shape**: Hit <Enter> to select the default shape, `dev` which runs on free Heroku dynos
* **Salesforce DX Configuration**: Enter a relative or absolute path to your JWT private key file and paste the Client ID.  NOTE: The JWT path cannot currently use ~ to refer to the user's home directory.

The command will run for about 5 minutes to get everything set up for you on Heroku.  When done, an admin user is generated with the password you provided and the MetaCI site is automatically connected to `metaci`.

App Shapes
==========

`metaci` can deploy three different app shapes for running your MetaCI site on Heroku:

* **dev**: Run with a build concurrency of one on free Heroku Dynos
* **staging**: Run with a fixed number of build workers (N) on paid Heroku dynos for build concurrency of N
* **prod**: Run on paid Heroku dynos with auto scaling via Hirefire.io (requires additional configuration)

Adding the Repository to MetaCI
-------------------------------

MetaCI needs to know about your repository, so the first thing we need to do is configure the repository in MetaCI:

.. code-block:: console

    $ metaci repo add

That was easy!  Since `metaci` sits on top of CumulusCI, it has access to everything CumulusCI already knows about your project.  As a result, we can prompt you for only the things we really need to prompt you for.

You can verify with:

.. code-block:: console

    $ metaci repo list

Adding Services
---------------

MetaCI needs to have the configuration for any CumulusCI services needed by your build flows.  For this demo, we'll just need the `github` service which we can add via `metaci`:

.. code-block:: console

    $ metaci service add --name github

You can verify with:

.. code-block:: console

    $ metaci service list

Adding Orgs
-----------

MetaCI needs the org information from the CumulusCI keychain for any orgs it will run builds against.  For our builds, we'll need to add 3 orgs:

.. code-block:: console

    $ metaci org add --name beta
    $ metaci org add --name feature
    $ metaci org add --name packaging

You can verify with:

.. code-block:: console

    $ metaci org list

Configuring Plans
-----------------

Plans are the core of MetaCI and represent a predefined set of tasks to run against a particular Salesforce org configuration.  In this section, we'll configure our repository to run in the three default plans that come with MetaCI.

Let's start by verifying that we can talk to MetaCI from `metaci` and look at the default plans that come with MetaCI:

.. code-block:: console

    $ metaci plan list
    MetaCI CLI v0.1.0
    
    #     Status                   Org          Flows                    Trigger Regex
    3     Beta Test                beta         ci_beta                  tag     beta/.*
    1     Feature Test             feature      ci_feature               commit  feature/.*
    2     Upload Beta              packaging    ci_master,release_beta   commit  master

The three default plans actually do quite a bit for us:

* **Feature Test**: Deploys the unmanaged metadata and all its dependencies into a scratch org created with the `feature` org config (located in `orgs/feature.json` in the repo) and runs all Apex tests.  Collects and records Apex Limits Usage for all Apex tests.  Triggered by any commit to any branch starting with `feature/`.
* **Upload Beta**: Deploys the package metadata and all its dependencies into the packaging org and deletes any stale metadata still in the package but not in the commit being deployed.  Then runs the `release_beta` flow to upload a beta release from the packaging org, create a tag and release on Github, and generate and publish release notes on the Github release.  Triggered on any commit to master.
* **Beta Test**: Installs the latest beta and all its dependencies into a scratch org created with the `beta` org config (located in `orgs/beta.json` in the repo) and runs all Apex tests.  Collects and records Apex Limits Usage for all Apex tests.  Triggered on new tags starting with `beta/`

Since Plans in MetaCI are abstract and can apply to multiple repositories, we separate Plans from the repositories they run against.  This makes it easy to add our local repository to all three of the standard build plans:

.. code-block:: console

    $ metaci plan repo_add 1
    $ metaci plan repo_add 2
    $ metaci plan repo_add 3

We can verify that the repository was added to all the plans with:

.. code-block:: console

    $ metaci plan repo_list 1
    $ metaci plan repo_list 2
    $ metaci plan repo_list 3

Running and Managing Builds
---------------------------

Our First Failing Build
=======================

CI is all about detecting and alerting us about failures, so let's start by creating our first failing build.  To do this, we'll use the `master` branch of our repository which currently does not have the CumulusCI configuration.  As a result, MetaCI should error early in the build:

.. code-block:: console

    $ git checkout master
    $ metaci plan run 1

The `metaci plan run <plan_id>` will kick off a build for the specified plan against the HEAD remote commit of your local git branch.  In this case, it kicked off a build of the `master` branch's latest commit in Github.  You can see the build in the build list:

.. code-block:: console
   
    $ metaci build list

You can also get the metadata about the build, the build log, and the logs from CumulusCI flows run by the build:

.. code-block:: console

    $ metaci build info 1
    $ metaci build info 1 --log
    $ metaci build info 1 --flow-log

Once our build fails, we can easily see the cause of the failure:

.. code-block:: console

    $ metaci build info 1 --log
    2017-10-27 22:34:00: -- Building commit cfd740bf94a964274d8420a6715b6542dd59e76a
    2017-10-27 22:34:00: -- Download commit from URL: https://github.com/SalesforceFoundation/MetaCI-DF17-Demo-Project/archive/cfd740bf94a964274d8420a6715b6542dd59e76a.zip
    2017-10-27 22:34:00: -- Extracting zip to temp dir /tmp/tmpt9RBIw
    2017-10-27 22:34:00: -- Commit extracted to build dir: /tmp/tmpt9RBIw/MetaCI-DF17-Demo-Project-cfd740bf94a964274d8420a6715b6542dd59e76a
    2017-10-27 22:34:00: The file cumulusci.yml was not found in the repo root: /tmp/tmpt9RBIw/MetaCI-DF17-Demo-Project-cfd740bf94a964274d8420a6715b6542dd59e76a
    2017-10-27 22:34:00: Deleting build dir /tmp/tmpt9RBIw/MetaCI-DF17-Demo-Project-cfd740bf94a964274d8420a6715b6542dd59e76a

To fix this error, let's go through the CumulusCI flow to merge our feature branch into master:

.. code-block:: console

    $ git checkout feature/cumulusci
    $ git push --set-upstream origin feature/cumulusci

Since we just pushed a new commit to our feature branch, we should have another build running:

.. code-block:: console

    $ metaci build list

Monitor the build until it completes and we should have our first passing build.  Now go to your forked repository in github and create a new Pull Request from your `feature/cumulusci` branch.

When viewing the created pull request, you should see the green build status above the green `Merge` button.  Click the `Merge` button to merge the branch into master.

Now, let's jump back to the CLI an monitor the new master build that kicked off as a result of this:

.. code-block:: console

    $ metaci build list

Note that this time were running the `Upload Beta` plan.  When that plan completes, we should see a Github release in the repository and another build of the `Beta Test` plan should be automatically triggered.

MetaCI's Web UI
---------------

Thus far we've been working exclusively in `metaci` on the command line.  But everything we've been doing has been generating real builds on a real web app.  So, why not end with taking a look around in a browser?:

.. code-block:: console

    $ metaci build browser 3
    $ metaci site browser
    $ metaci repo browser

MetaCI's Web Admin UI
=====================

Go to https://<your_app_name>.herokuapp.com/admin and log in using the admin password you set during **metaci site create**.  The MetaCI Web Admin UI provides access to view all data in your MetaCI instance's database.

Configuring Github Authentication
=================================

If you want to have users log in via their Github credentials and be able to elevate certain users to see Private builds, you need to configure a Github OAuth App.  MetaCI uses the django-allauth package to handle OAuth logins which can be configured with the following steps:

* Create a Github OAuth App per the instructions here: http://django-allauth.readthedocs.io/en/latest/providers.html#github  MetaCI only needs access to the user information and email for the OAuth application.  No repository rights are needed from the user.
* Go to the MetaCI Admin UI 
* Go to Social Accounts -> Social Applications and click the **Add** button
* Select **GitHub** as the provider, enter the client id and secret key from the Github OAuth App you created, and add the default site to **Chosen Sites**

Github logins should now be configured.  Click **View Site** at the top right of the admin page to return to the site.  Click **Log Out** and try to **Log In** with your Github user.  You should be prompted to grant access to your Github profile and then logged into MetaCI as your Github user.

When you first login as your Github user, you will not have any elevated permissions to do anything special in MetaCI.  To grant yourself permissions, click **Log Out** and follow the steps below to grant your Github user **Supervisor status**.

Granting Permissions to a Github User
=====================================

There are two main user roles which can be granted to individual users:

* **Staff status**: Staff users can view Private builds, rebuild failed builds, and run new builds.  Staff users are also allowed to use the full text search to search builds.
* **Superuser status**: Superusers can access the MetaCI Admin UI and manipulate records.  Superusers can also use the MetaCI REST API which is required for use of the MetaCI CLI.

In the Admin UI, go to Users -> Users and click the username's name from the list.  Use the **Staff status** and **Superuser status** checkboxes to grant permissions to the user.

