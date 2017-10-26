# -*- coding: utf-8 -*-

"""org command subgroup for metaci CLI"""

import click
import coreapi
import json
import webbrowser
from cumulusci.core.config import ScratchOrgConfig
from cumulusci.core.exceptions import OrgNotFound
from metaci_cli.cli.commands.main import main
from metaci_cli.cli.util import check_current_site
from metaci_cli.cli.util import lookup_repo
from metaci_cli.cli.util import render_recursive
from metaci_cli.cli.util import require_project_config
from metaci_cli.cli.config import pass_config
from metaci_cli.metaci_api import ApiClient

@click.group('org')
def org():
    pass

def prompt_org_name(repo_id, name, api_client, retry=None):
    if name is None:
        raise ValueError('name must be a string not None')

    # Check for existing org with name
    params = {
        'name': name,
        'repo': repo_id,
    }
    
    res = api_client('orgs','list', params=params)
    if res['count'] > 0:
        if retry is False:
            raise click.ClickException('A MetaCI org named {} already exists for this repository'.format(name))
        else:
            click.echo('A MetaCI org named {} already exists for this repository.  Please select a different name'.format(name))
            name = click.prompt('Org Name') 
            return prompt_org_name(repo_id, name, api_client, retry=False)
    return name

@click.command(name='browser', help='Opens the org on the MetaCI site in a browser tab')
@click.argument('org_name')
@pass_config
def org_browser(config, org_name):
    api_client = ApiClient(config)

    params = {
        'name': org_name,
    }

    # Look up the build
    res = api_client('orgs', 'list', params=params)
    if res['count'] == 0:
        raise click.ClickException('Org named {} not found.  Use metaci org list to see a list of available org names'.format(org_name))

    service = check_current_site(config)
    url = '{}/orgs/{}'.format(service.url, res['results'][0]['id'])
    click.echo('Opening browser to {}'.format(url))
    webbrowser.open(url)

@click.command(name='add', help='Create a MetaCI org from a local cci keychain org')
@click.option('--name', help="Override the org name (defaults to the cci keychain org name)")
@click.option('--org', help="Specify the org name from your local cci keychain to create in MetaCI")
@click.option('--repo', help="Specify the repo in format OwnerName/RepoName")
@pass_config
def org_add(config, name, org, repo):
    require_project_config(config)

    api_client = ApiClient(config)
    params = {}

    # Prompt for org name if not specified
    if not org:
        click.echo('To create a MetaCI org, select one of your existing CumulusCI orgs.  The org information from your local CumulusCI keychain will be transferred to the MetaCI site.  You can use cci org scratch or cci org connect to create new CumulusCI orgs if needed.')
        click.echo()
        default_org, org_config = config.keychain.get_default_org()
        click.echo('Available Orgs: ' + ', '.join(config.keychain.list_orgs()))
        org = click.prompt('Org', default=default_org)

    # Validate the org
    try:
        org_config = config.keychain.get_org(org)
    except OrgNotFound:
        raise click.ClickException('The org {} is not configured in the local cci keychain'.format(org))

    org_name = name
    if not name:
        org_name = org

    # Filter by repository
    repo_data = lookup_repo(api_client, config, repo, required=True)
   
    name = prompt_org_name(repo_data['id'], org_name, api_client) 

    params['repo_id'] = repo_data['id']
    params['name'] = name
    params['scratch'] = isinstance(org_config, ScratchOrgConfig)
    
    if params['scratch']: 
        clean_org_config = {
            'config_file': org_config.config_file,
            'config_name': org_config.config_name,
            'namespaced': org_config.namespaced,
            'scratch': org_config.scratch,
        }
    else:
        clean_org_config = org_config.config

    params['json'] = json.dumps(clean_org_config)

    res = api_client('orgs', 'create', params=params)
    click.echo()
    click.echo('Org {} was successfully created.  Use metaci org info {} to see the org details.'.format(name, name))


@click.command(name='info', help='Show info on a single org')
@click.argument('name')
@click.option('--repo', help="Specify the repo in format OwnerName/RepoName")
@pass_config
def org_info(config, name, repo):
    api_client = ApiClient(config)

    params = {
        'name': name
    }

    # Filter by repository
    repo_data = lookup_repo(api_client, config, repo, required=True)
    params['repo'] = repo_data['id']

    # Look up the org
    res = api_client('orgs', 'list', params=params)
    if res['count'] == 0:
        raise click.ClickError('Org named {} not found'.format(name))

    click.echo(render_recursive(res['results'][0]))
   
 
@click.command(name='list', help='Lists orgs')
@click.option('--repo', help="Specify the repo in format OwnerName/RepoName")
@pass_config
def org_list(config, repo):
    api_client = ApiClient(config)

    params = {}

    # Filter by repository
    repo_data = lookup_repo(api_client, config, repo)
    if repo_data:
        params['repo'] = repo_data['id']

    res = api_client('orgs', 'list', params=params)

    org_list_fmt = '{id:<5} {name:24.24} {scratch:7} {repo[owner]}'
    headers = {
        'id': '#',
        'name': 'Name',
        'scratch': 'Scratch',
        'repo': {'owner': 'Repo'},
    }
    click.echo(org_list_fmt.format(**headers))
    #org_list_fmt += "/{repo[name]}"
    for org in res['results']:
        click.echo(org_list_fmt.format(**org))


org.add_command(org_browser)
org.add_command(org_add)
org.add_command(org_info)
org.add_command(org_list)
main.add_command(org)
