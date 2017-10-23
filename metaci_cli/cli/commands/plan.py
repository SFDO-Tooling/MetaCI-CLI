# -*- coding: utf-8 -*-

"""Console script for metaci_cli."""

import click
from metaci_cli.cli.commands.main import main
from metaci_cli.cli.util import get_repo_id
from metaci_cli.cli.util import render_ordered_dict
from metaci_cli.cli.config import pass_config
from metaci_cli.metaci_api import ApiClient

@click.group('plan')
def plan():
    pass

def prompt_org(api_client, config, repo_id):
    params = {'repo': repo_id}
    res = api_client('orgs', 'list', params=params)
    orgs = {}
    for org in res['results']:
        orgs[org['name']] = org['id']
    orgs = orgs.keys()
    orgs.sort()

    click.echo('Valid org choices: {}'.format(', '.join(org_keys)))
    org = click.prompt('Org')
    if org not in orgs.keys():
        raise click.UsageError('Org {} not found.  Check metaci org list.'.format(org))
    return org

@click.command(name='create', help='Create a new Plan to run builds on MetaCI')
@pass_config
def plan_create(config):
    if not config.project_config:
        raise click.UsageError('You must be inside a local git repository configured for CumulusCI.  No CumulusCI configuration was detected in the local directory')

    api_client = ApiClient(config)

    params = {}

    # Filter by repository
    repo_id = get_repo_id(api_client, config, None, required=True)
    params['repo'] = repo_id

    name = click.prompt('Name')
    description = click.prompt('Description')
    org = prompt_org(api_client, config, repo_id)
    flows_list = config.project_config.flows.keys()
    flows_list.sort()
    click.echo('Available Flows: {}'.format(', '.join(flows_list)))
    flows = click.prompt('Flows (separate multiple with commas)')
    trigger_type = click.prompt('Trigger Type (commit, tag, or manual)')
    regex = click.prompt('Branch/Tag Match RegEx (ex feature/.*)')
    context = None
    if click.prompt('Set commit status in Github for Plan?'):
        context = click.prompt('Github Commit Status Context', default=name)
    active = click.confirm('Active?')
    public = click.confirm('Public?')
        

    params = {
        'name': name,    
        'description': description,    
        'org': org,    
        'flows': flows,    
        'type': trigger_type,    
        'regex': regex,    
        'context': context,    
        'active': active,    
        'public': public,    
        'repo_id': repo_id,    
    }

    res = api_client('plans', 'create', params=params)


@click.command(name='list', help='Lists plans')
@click.option('--repo', help="Specify the repo in format OwnerName/RepoName")
@pass_config
def plan_list(config, repo):
    api_client = ApiClient()

    params = {}

    # Filter by repository
    repo_id = get_repo_id(api_client, config, repo)
    if repo_id:
        params['repo'] = repo_id

    res = api_client('plans', 'list', params=params)

    plan_list_fmt = '{id:5} {name:24.24} {org:12.12} {flows:24.24} {type:7.7} {regex}'
    headers = {
        'id': '#',
        'name': 'Status',
        'org': 'Org',
        'flows': 'Flows',
        'type': 'Trigger',
        'regex': 'Regex',
    }
    click.echo(plan_list_fmt.format(**headers))
    for plan in res['results']:
        click.echo(plan_list_fmt.format(**plan))

plan.add_command(plan_create)
plan.add_command(plan_list)
main.add_command(plan)
