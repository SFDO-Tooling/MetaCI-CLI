.. highlight:: shell

=====
Usage
=====

For all `metaci` commands, you will need to start from inside a local clone of a Github repository that is already configured for CumulusCI.

Connecting to MetaCI
--------------------

`metaci` requires a connection to a running instance of MetaCI.  This is typically a MetaCI site running on Heroku though `metaci` can also connect to a local MetaCI development site.  `metaci` only has a single connection to a single site.  If you need to work with multiple sites, you need to re-run `metaci site connect` each time you need to switch sites.

Launching a New MetaCI Site on Heroku
-------------------------------------

If you want to launch a new instance of MetaCI on Heroku, use the `metaci site add` command which will prompt for some information then deploy a new instance of MetaCI on Heroku for you.  After the site is deployed, an initial admin user will be created for you and the site will be linked with `metaci` automatically.

Connecting to an Existing MetaCI Site
-------------------------------------

To connect to an existing site, you will need to get a MetaCI API token for your user account in the MetaCI site.  Typically, users would request this from their admin.  If you are the admin and are running on heroku, you can get a token for a user by running:

.. code-block:: console

    $ heroku run python manage.py usertoken <username>

To connect to a MetaCI site once you have the API token:

.. code-block:: console

    $ metaci site connect

Command Structure
-----------------

The main `metaci` command will return a list of command groups:

.. code-block:: console

    Usage: metaci [OPTIONS] COMMAND [ARGS]...
    
    Console script for metaci_cli.
    
    Options:
      --help  Show this message and exit.
    
    Commands:
      build
      org
      plan
      repo
      service
      site

You can get a list of commands inside each group by calling the group:

.. code-block:: console
    $ metaci repo
    MetaCI CLI v0.1.0
    
    Usage: metaci repo [OPTIONS] COMMAND [ARGS]...
    
    Options:
      --help  Show this message and exit.
    
    Commands:
      add      Create a MetaCI repository from a local git...
      browser  Opens the repo on the MetaCI site in a...
      info     Show info on a single repo
      list     Lists repositories

You can get all available arguments and options on a command with `--help`:

.. code-block:: console
   $ metaci repo add --help
   MetaCI CLI v0.1.0

   Usage: metaci repo add [OPTIONS]

     Create a MetaCI repository from a local git repository

   Options:
     --repo TEXT  Specify the repo in format OwnerName/RepoName
     --url TEXT   Specify the repo base url instead of prompting
     --public     Should this repository's builds and plans be visible to
                  anonymous users?
     --help       Show this message and exit.

