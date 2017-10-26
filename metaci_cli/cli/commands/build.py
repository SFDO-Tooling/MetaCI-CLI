# -*- coding: utf-8 -*-

"""build command subgroup for metaci CLI"""

import click
import coreapi
import webbrowser
from metaci_cli.cli.commands.main import main
from metaci_cli.cli.util import color_status
from metaci_cli.cli.util import check_current_site
from metaci_cli.cli.util import lookup_repo
from metaci_cli.cli.util import render_recursive
from metaci_cli.cli.config import pass_config
from metaci_cli.metaci_api import ApiClient

@click.group('build')
def build():
    pass

@click.command(name='browser', help='Opens the build on the MetaCI site in a browser tab')
@click.argument('build_id')
@pass_config
def build_browser(config, build_id):
    api_client = ApiClient(config)

    params = {
        'id': build_id,
    }

    # Look up the build
    try:
        res = api_client('builds', 'read', params=params)
    except coreapi.exceptions.ErrorMessage as e:
        raise click.ClickException('Build with id {} not found.  Use metaci build list to see a list of latest builds and their ids'.format(build_id))

    service = check_current_site(config)
    url = '{}/builds/{}'.format(service.url, res['id'])
    click.echo('Opening browser to {}'.format(url))
    webbrowser.open(url)
    
@click.command(name='info', help='Show info on a single build')
@click.argument('build_id')
@click.option('--log', is_flag=True, help="If set, only outputs the build log")
@click.option('--flow-log', is_flag=True, help="If set, only outputs logs from all CumulusCI flows run by this build")
@click.option('--flow', help="Used with --flow-log, limits the log output to only the specified flow")
@pass_config
def build_info(config, build_id, log, flow_log, flow):
    api_client = ApiClient(config)

    params = {
        'id': build_id,
    }

    # Look up the build
    try:
        build_res = api_client('builds', 'read', params=params)
    except coreapi.exceptions.ErrorMessage as e:
        raise click.ClickException('Build with id {} not found.  Use metaci build list to see a list of latest builds and their ids'.format(build_id))

    if log:
        click.echo(build_res['log'])
    elif flow_log:
        params = {
            'build': build_id
        }
        if flow:
            params['flow'] = flow
        build_flow_res = api_client('build_flows', 'list', params=params)
        for build_flow in build_flow_res['results']:
            click.echo()
            click.echo(click.style('{}:'.format(build_flow['flow']), bold=True, fg='blue'))
            click.echo(build_flow['log'])
        
    else:
        click.echo(render_recursive(build_res))

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
    

build.add_command(build_browser)
build.add_command(build_info)
build.add_command(build_list)
main.add_command(build)
