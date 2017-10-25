# -*- coding: utf-8 -*-

"""repo command subgroup for metaci CLI"""

import click
import json
from metaci_cli.cli.commands.main import main
from metaci_cli.cli.util import lookup_repo
from metaci_cli.cli.util import render_recursive
from metaci_cli.cli.util import require_project_config
from metaci_cli.cli.config import pass_config
from metaci_cli.metaci_api import ApiClient

@click.group('repo')
def repo():
    pass

def check_existing_repo(owner, name, api_client):
    if owner is None:
        raise ValueError('owner must be a string not None')
    if name is None:
        raise ValueError('name must be a string not None')
    # Check for existing repo with owner/name
    params = {
        'owner': owner,
        'name': name,
    }
    res = api_client('repos','list', params=params)
    if res['count'] > 0:
        raise click.ClickException('A MetaCI repository named {} already exists'.format(name))
    return owner, name

@click.command(name='create', help='Create a MetaCI repository from a local git repository')
@click.option('--repo', help="Specify the repo in format OwnerName/RepoName")
@click.option('--url', help="Specify the repo base url instead of prompting")
@click.option('--public', is_flag=True, default=False, help="Should this repository's builds and plans be visible to anonymous users?")
@pass_config
def repo_create(config, repo, url, public):
    require_project_config(config)

    api_client = ApiClient(config)

    # Prompt for repo owner and name if not specified
    if not repo:
        click.echo()
        click.echo('Enter a Github repository owner and name.  Example: for the repository https://github.com/OwnerName/RepoName, the owner is OwnerName and the repo name is RepoName.  Repository owner can be either a Github username or a Github organization')
        owner = click.prompt('Owner')
        name = click.prompt('Name')
    else:
        parts = repo.split('/')
        if len(parts) != 2:
            raise click.ClickException('--repo must be in the format OwnerName/RepoName')
        owner = parts[0]
        name = parts[1]

    # Validate the repo
    check_existing_repo(owner, name, api_client) 

    if not url:
        url = 'https://github.com/{}/{}'.format(owner, name)
        url = click.prompt('Repo URL', default=url)

    click.echo()
    click.echo('# Public or Private?')
    click.echo('On a repository set to public, all public plans and builds of those plans are visible to anonymous users.  Private repository plans and builds are only visible to logged in users with the is_staff role granted by an admin.')
    public = click.confirm('Public?')
    
    params = {
        'owner': owner,
        'name': name,
        'url': url,
        'public': public,
    }

    res = api_client('repos', 'create', params=params)
    click.echo()
    click.echo('Repository {}/{} was successfully created with the following config'.format(owner, name))
    render_recursive(res)


@click.command(name='info', help='Show info on a single repo')
@click.option('--repo', help="Specify the repo in format OwnerName/RepoName")
@pass_config
def repo_info(config, repo):
    api_client = ApiClient(config)
    # Look up repository
    repo = lookup_repo(api_client, config, repo, required=True)
    click.echo(render_recursive(repo))


@click.command(name='list', help='Lists repositories')
@click.option('--owner', help="List all repositories with a given owner organization or username")
@click.option('--repo', help="Specify the repo in format OwnerName/RepoName")
@pass_config
def repo_list(config, owner, repo):
    api_client = ApiClient(config)

    params = {}
    if owner:
        params['owner'] = owner
    res = api_client('repos', 'list', params=params)

    repo_list_fmt = '{id:<3} {owner:20.20} {name:20.20} {public:7} {url}'
    headers = {
        'id': '#',
        'owner': 'Owner',
        'name': 'Name',
        'public': 'Public?',
        'url': 'Repo URL',
    }
    click.echo(repo_list_fmt.format(**headers))
    for repo in res['results']:
        click.echo(repo_list_fmt.format(**repo))

repo.add_command(repo_create)
repo.add_command(repo_info)
repo.add_command(repo_list)
main.add_command(repo)
