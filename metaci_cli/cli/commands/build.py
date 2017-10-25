# -*- coding: utf-8 -*-

"""build command subgroup for metaci CLI"""

import click
from metaci_cli.cli.commands.main import main
from metaci_cli.cli.util import color_status
from metaci_cli.cli.util import lookup_repo
from metaci_cli.cli.util import render_recursive
from metaci_cli.cli.config import pass_config
from metaci_cli.metaci_api import ApiClient

@click.group('build')
def build():
    pass

@click.command(name='info', help='Show info on a single build')
@click.argument('build_id')
@pass_config
def build_info(config, build_id):
    api_client = ApiClient(config)

    params = {
        'id': build_id,
    }

    # Look up the build
    res = api_client('orgs', 'list', params=params)
    if res['count'] == 0:
        raise click.ClickError('Org named {} not found'.format('name'))

    click.echo(render_recursive(res['results'][0]))

@click.command(name='list', help='Lists builds')
@click.option('--repo', help="Specify the repo in format OwnerName/RepoName")
@click.option('--status', help="Filter by build status, options: queued, waiting, in_progress, success, failed, error")
@pass_config
def build_list(config, repo, status):
    api_client = ApiClient(config)

    params = {}

    # Filter by repository
    repo_data = lookup_repo(api_client, config, repo)
    if repo_data:
        params['repo'] = repo_data['id']

    # Filter by status
    if status:
        params['status'] = status

    res = api_client('builds', 'list', params=params)

    build_list_fmt = '{id:<5} {status:8.8} {plan[name]:24.24} {branch[name]:24.24} {commit}'
    headers = {
        'id': '#',
        'status': 'Status',
        'plan': {'name': 'Plan'},
        'branch': {'name': 'Branch'},
        'commit': 'Commit',
    }
    click.echo(build_list_fmt.format(**headers))
    for build in res['results']:
        click.echo(
            color_status(
                status = build['status'],
                line = build_list_fmt.format(**build),
            )
        )
    

build.add_command(build_info)
build.add_command(build_list)
main.add_command(build)
