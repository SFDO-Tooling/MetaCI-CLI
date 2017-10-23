# -*- coding: utf-8 -*-

"""Console script for metaci_cli."""

import click
import json
import webbrowser
from cumulusci.core.config import ServiceConfig
from cumulusci.core.exceptions import ServiceNotConfigured
from metaci_cli.cli.commands.main import main
from metaci_cli.cli.util import render_ordered_dict
from metaci_cli.cli.config import pass_config

@click.group('site')
def site():
    pass

def verify_overwrite(config):
    try:
        service = config.keychain.get_service('metaci')
    except ServiceNotConfigured:
        return

    click.echo('Site {} is currently configured.  Connecting to a new site will delete the local configuration for the current site.  You can always use metaci site connect to reconnect to an existing site.'.format(service.url))
    click.confirm(
        click.style(
            'Are you sure you want to connect to a new site?',
            bold=True,
            fg='red',
        ),
        abort=True
    )
    return service

def check_current_site(config):
    try:
        service = config.keychain.get_service('metaci')
    except ServiceNotConfigured:
        raise click.UsageError('No site is currently connected.  Use metaci site connect or metaci site create to connect to a site')
    return service

@click.command(name='browser', help='Opens the MetaCI site in a browser tab')
@pass_config
def site_browser(config):
    service = check_current_site(config)
    click.echo('Opening browser to {}'.format(service.url))
    webbrowser.open(service.url)

@click.command(name='create', help='Deploy a new Heroku app running MetaCI')
@pass_config
def site_create(config):
    pass

@click.command(name='connect', help='Connects to an existing MetaCI instance')
@pass_config
def site_connect(config):
    verify_overwrite(config)
    url = click.prompt('Site Base URL')
    click.echo('Contact your MetaCI administrator to get an API Token.  Tokens can be created by administrators in the admin panel under Auth Tokens -> Tokensi.')
    token = click.prompt('API Token')
    service = ServiceConfig({
        'url': url,
        'token': token,
    })
    config.keychain.set_service('metaci', service)

@click.command(name='info', help='Displays info about the current MetaCI site')
@pass_config
def site_info(config):
    service = check_current_site(config)
    render_ordered_dict(service.config)


site.add_command(site_browser)
site.add_command(site_create)
site.add_command(site_connect)
site.add_command(site_info)
main.add_command(site)
