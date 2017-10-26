# -*- coding: utf-8 -*-

"""service command subgroup for metaci CLI"""

import click
import coreapi
import json
import webbrowser
from cumulusci.core.exceptions import ServiceNotConfigured
from cumulusci.core.exceptions import ServiceNotValid
from metaci_cli.cli.commands.main import main
from metaci_cli.cli.util import check_current_site
from metaci_cli.cli.util import lookup_repo
from metaci_cli.cli.util import render_recursive
from metaci_cli.cli.util import require_project_config
from metaci_cli.cli.config import pass_config
from metaci_cli.metaci_api import ApiClient

@click.group('service')
def service():
    pass

def prompt_service_name(name, api_client):
    if name is None:
        raise ValueError('name must be a string not None')

    # Check for existing service with name
    params = {
        'name': name,
    }
    
    res = api_client('services','list', params=params)
    if res['count'] > 0:
        raise click.ClickException('A MetaCI service named {} already exists'.format(name))
    return name

@click.command(name='browser', help='Opens the service on the MetaCI site in a browser tab')
@click.argument('name')
@pass_config
def service_browser(config, name):
    api_client = ApiClient(config)

    params = {
        'name': name,
    }

    # Look up the build
    res = api_client('services', 'list', params=params)
    if res['count'] == 0:
        raise click.ClickException('Service named {} not found.  Use metaci service list to see a list of available service names'.format(name))

    metaci_service = check_current_site(config)
    url = '{}/admin/cumulusci/service/{}'.format(metaci_service.url, res['results'][0]['id'])
    click.echo('Opening browser to {}'.format(url))
    webbrowser.open(url)

@click.command(name='add', help='Create a MetaCI service from a local cci keychain service')
@click.option('--name', help="Specify the service name from your local cci keychain to create in MetaCI")
@pass_config
def service_add(config, name):
    require_project_config(config)

    api_client = ApiClient(config)

    services = config.keychain.list_services()
    existing = []
    resp = api_client('services','list')
    for service in resp['results']:
        existing.append(service['name'])
        if service['name'] in services:
            services.remove(service['name'])

    # Prompt for service name if not specified
    if not name:
        click.echo('To create a MetaCI service, select one of your existing CumulusCI services.  The service information from your local CumulusCI keychain will be transferred to the MetaCI site.  You can use cci service list to see available services and cci service connect <service_name> to connect a service to the local cci keychain.')
        click.echo()
        click.echo('Available Services: ' + ', '.join(services))
        name = click.prompt('Service')

    # Validate the service name
    if name not in services:
        if name in existing:
            raise click.ClickException('Service {} already exists.  Available services are: {}'.format(name, ', '.join(services)))
        raise click.ClickException('Service {} is invalid.  Available services are: {}'.format(name, ', '.join(services)))

    # Validate the service exists in the cci keychain
    try:
        service_config = config.keychain.get_service(name)
    except ServiceNotConfigured:
        raise click.ClickException('The service {} is not configured in the local cci keychain.  Use cci service connect {}'.format(service, service))
    except ServiceNotValid:
        raise click.ClickException('The service {} is not a valid cci service name.  If this is a custom service for the project, you need to first configure the service in the project cumulusci.yml file.'.format(service))

    params = {}
    params['name'] = name
    params['json'] = json.dumps(service_config.config)
    res = api_client('services', 'create', params=params)
    click.echo()
    click.echo('Service {} was successfully created.  Use metaci service info {} to see the service details.'.format(name, name))


@click.command(name='info', help='Show info on a service')
@click.argument('name')
@pass_config
def service_info(config, name):
    api_client = ApiClient(config)

    params = {
        'name': name
    }

    # Look up the service
    res = api_client('services', 'list', params=params)
    if res['count'] == 0:
        raise click.ClickError('Service named {} not found'.format(name))

    click.echo(render_recursive(res['results'][0]))
   
 
@click.command(name='list', help='Lists services')
@pass_config
def service_list(config):
    api_client = ApiClient(config)

    params = {}
    res = api_client('services', 'list', params=params)

    service_list_fmt = '{id:<3} {name}'
    headers = {
        'id': '#',
        'name': 'Name',
    }
    click.echo(service_list_fmt.format(**headers))
    for service in res['results']:
        click.echo(service_list_fmt.format(**service))


service.add_command(service_browser)
service.add_command(service_add)
service.add_command(service_info)
service.add_command(service_list)
main.add_command(service)
