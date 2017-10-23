# -*- coding: utf-8 -*-

"""Command line utils for metaci"""

import click
import requests
from collections import OrderedDict

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
    elif status == 'failed':
        output = click.style(line, fg='yellow')
        output += click.style('', reset=True)
    elif status == 'error':
        output = click.style(line, fg='red')
        output += click.style('', reset=True)
    return output

def get_repo_id(api_client, config, repo=None, required=None):
    repo_info = {
        'name': None,
        'owner': None,
    }

    # Parse repo string from CLI option in formation OwnerName/RepoName
    if repo:
        parts = repo.split('/')
        if parts != 2:
            raise click.UsageError('--repo must use the format OwnerName/RepoName')
        repo_info['owner'] = parts[0]
        repo_info['name'] = parts[1]

    repo_id = None

    # If in a cci project git repo, auto filter that repo by default
    if config.project_config:
        repo_info['name'] = config.project_config.repo_name
        repo_info['owner'] = config.project_config.repo_owner
    if repo_info['name'] and repo_info['owner']:
        res = api_client('repos', 'list', params=repo_info)
        if res['count'] == 1:
            repo_id = res['results'][0]['id']
   
    if required and not repo_id: 
        if config.project_config.repo_user:
            raise click.UsageError('You are in a CumulusCI project but it appears the repository is not yet configured in MetaCI.  Use `metaci repo create` to add the repo.  You can also use --repo OwnerName/RepoName to manually specify a repository')
        elif repo:
            raise click.UsageError('Could not find repository {} in MetaCI.  Use metaci repo create to add the repo.  You can also use --repo OwnerName/RepoName to manually specify a repository.'.format(repo))
        else:
            raise click.UsageError('No repository specified.  You can use --repo OwnerName/RepoName or change directory into a local git repository configured for CumulusCI.')

    # Filter by repo
    if repo_id:
        repo_id = repo_id
        if not required:
            click.echo('Filtering on repository {owner}/{name}'.format(**repo_info))
            click.echo('')
    else:
        if repo_info['name'] and repo_info['owner'] and not required:
            click.echo('Failed to find repository {owner}/{name} in MetaCI.  Showing all repositories instead.'.format(**repo_info))

    return repo_id

def render_ordered_dict(od, indent=None):
    if indent is None:
        indent = 0
    indent_str = ' ' * indent
    for key, value in od.items():
        key_str = click.style(unicode(key) + ':', bold=True)
        if isinstance(value, OrderedDict):
            click.echo('{}{}'.format(indent_str, key_str))
            render_ordered_dict(value, indent=indent+2)
        else:
            click.echo('{}{} {}'.format(indent_str, key_str, value))

def require_project_config(config):
    if not config.project_config:
        raise click.UsageError('You must be in a CumulusCI configured git repository.  No CumulusCI project configuration could be detected')
