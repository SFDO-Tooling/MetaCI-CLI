# -*- coding: utf-8 -*-

"""metaci: The command line interface to MetaCI"""

import click
import metaci_cli
import requests
#from metaci_cli.cli.config import check_latest_version

# Check for latest version and notify user how to upgrade if new version exists
#try:
#    check_latest_version()
#except requests.exceptions.RequestException as e:
#    click.echo('Error checking cci version:')
#    click.echo(e.message)

@click.group()
def main():
    """Console script for metaci_cli."""
    click.echo("MetaCI CLI v{}".format(metaci_cli.__version__))
    click.echo()

if __name__ == "__main__":
    main()
