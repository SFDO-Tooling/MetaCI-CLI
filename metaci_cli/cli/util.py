# -*- coding: utf-8 -*-

"""Command line utils for metaci"""

import click
import requests
from collections import OrderedDict
from cumulusci.core.exceptions import NotInProject
from cumulusci.core.exceptions import ProjectConfigNotFound

def color_status(status, line=None):
    if not line:
        line = status
    output = line
    if status in ['queued','waiting','in_progress']:
        output = click.style(line, fg='cyan')
        output += click.style('', reset=True)
    elif status == 'success':
        output = click.style(line, fg='green')
        output += click.style('', reset=True)
    elif status == 'fail':
        output = click.style(line, fg='yellow')
        output += click.style('', reset=True)
    elif status == 'error':
        output = click.style(line, fg='red')
        output += click.style('', reset=True)
    return output

def check_current_site(config):
    try:
        service = config.keychain.get_service('metaci')
    except ServiceNotConfigured:
        raise click.UsageError('No site is currently connected.  Use metaci site connect or metaci site create to connect to a site')
    return service

def get_or_create_branch(api_client, name, repo_id):
    params = {
        'repo': 'id',
        'name': name,
    }
    resp = api_client('branches', 'list', params=params)
    if resp['count'] == 0:
        params = {
            'repo_id': repo_id,
            'name': name,
        }
        return api_client('branches', 'create', params=params)
    else:
        return resp['results'][0]

def lookup_repo(api_client, config, repo=None, required=None, no_output=None):
    repo_info = {
        'name': None,
        'owner': None,
    }

    # Parse repo string from CLI option in formation OwnerName/RepoName
    if repo:
        parts = repo.split('/')
        if len(parts) != 2:
            raise click.UsageError('--repo must use the format OwnerName/RepoName')
        repo_info['owner'] = parts[0]
        repo_info['name'] = parts[1]

    repo_data = None

    if not repo:
        # If in a cci project git repo, auto filter that repo by default
        try:
            if config.project_config:
                repo_info['name'] = config.project_config.repo_name
                repo_info['owner'] = config.project_config.repo_owner
        except NotInProject:
            pass
        except ProjectConfigNotFound:
            raise click.ClickException('Your local git repository does not appear to be configured for CumulusCI.  Configure CumulusCI for your project first using the documentation at http://cumulusci.readthedocs.io so you can use metaci on this repository.')
    
    if repo_info['name'] and repo_info['owner']:
        res = api_client('repos', 'list', params=repo_info)
        if res['count'] == 1:
            repo_data = res['results'][0]

    if required and not repo_data: 
        if config.project_config.repo_user:
            raise click.UsageError('You are in a CumulusCI project but it appears the repository is not yet configured in MetaCI.  Use `metaci repo create` to add the repo.  You can also use --repo OwnerName/RepoName to manually specify a repository')
        elif repo:
            raise click.UsageError('Could not find repository {} in MetaCI.  Use metaci repo create to add the repo.  You can also use --repo OwnerName/RepoName to manually specify a repository.'.format(repo))
        else:
            raise click.UsageError('No repository specified.  You can use --repo OwnerName/RepoName or change directory into a local git repository configured for CumulusCI.')

    # Filter by repo
    if repo_data:
        if not required and not no_output:
            click.echo(
                click.style(
                    '- Filtering on repository {owner}/{name}'.format(**repo_info),
                    fg='green',
                )
            )
    else:
        if repo_info['name'] and repo_info['owner'] and not required and not no_output:
            click.echo(
                click.style(
                    '- Failed to find repository {owner}/{name} in MetaCI.  Showing all repositories instead.'.format(**repo_info),
                    fg='red',
                )
            )

    return repo_data

def render_recursive(data, indent=None):
    if indent is None:
        indent = 0
    indent_str = ' ' * indent
    if isinstance(data, list):
        for item in data:
            render_recursive(item, indent=indent+2)
    elif isinstance(data, dict):
        for key, value in data.items():
            key_str = click.style(unicode(key) + ':', bold=True)
            if isinstance(value, list):
                render_recursive(value, indent=indent+2)
            elif isinstance(value, dict):
                click.echo('{}{}'.format(indent_str, key_str))
                render_recursive(value, indent=indent+2)
            else:
                click.echo('{}{} {}'.format(indent_str, key_str, value))

def require_project_config(config):
    if not config.project_config:
        raise click.UsageError('You must be in a CumulusCI configured git repository.  No CumulusCI project configuration could be detected')
