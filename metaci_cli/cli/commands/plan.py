# -*- coding: utf-8 -*-

"""Console script for metaci_cli."""

import click
import coreapi
import webbrowser
from metaci_cli.cli.commands.main import main
from metaci_cli.cli.util import check_current_site
from metaci_cli.cli.util import get_or_create_branch
from metaci_cli.cli.util import lookup_repo
from metaci_cli.cli.util import render_recursive
from metaci_cli.cli.config import pass_config
from metaci_cli.metaci_api import ApiClient

def get_plan(api_client, plan_id):
    """ Workaround for a bug in plans read which causes failure when looking up by plan id """
    params = {
        'id': plan_id
    }

    # Look up the plan
    res = api_client('plans', 'list', params=params)
    if res['count'] == 0:
        raise click.ClickException('Plan with id {} not found. Use metaci plan list to see a list of plans and their ids'.format(plan_id))

    return res['results'][0]

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

    click.echo('Valid org choices: {}'.format(', '.join(orgs)))
    org = click.prompt('Org')
    if org not in orgs:
        raise click.UsageError('Org {} not found.  Check metaci org list.'.format(org))
    return org

@click.command(name='browser', help='Opens the plan on the MetaCI site in a browser tab')
@click.argument('plan_id')
@pass_config
def plan_browser(config, plan_id):
    api_client = ApiClient(config)

    params = {
        'id': plan_id,
    }

    # Look up the plan
    try:
        res = api_client('plans', 'read', params=params)
    except coreapi.exceptions.ErrorMessage as e:
        raise click.ClickException('Plan with id {} not found.  Use metaci plan list to see a list of plans and their ids'.format(plan_id))

    service = check_current_site(config)
    url = '{}/plans/{}'.format(
        service.url,
        res['id'],
    )
    click.echo('Opening browser to {}'.format(url))
    webbrowser.open(url)

@click.command(name='add', help='Create a new Plan to run builds on MetaCI')
@pass_config
def plan_add(config):
    if not config.project_config:
        raise click.UsageError('You must be inside a local git repository configured for CumulusCI.  No CumulusCI configuration was detected in the local directory')

    api_client = ApiClient(config)

    params = {}

    # Make sure the local repo exists
    repo_data = lookup_repo(api_client, config, None, required=True)

    click.echo('# Name and Description')
    click.echo('Provide a name and description of the build plan you are creating')
    name = click.prompt('Name')
    description = click.prompt('Description')

    click.echo()
    click.echo('# Org')    
    click.echo('Select the MetaCI org this plan should run its builds against.  If the org does not yet exist, use metaci org create to create the org first.')
    org = prompt_org(api_client, config, repo_data['id'])

    flows_list = config.project_config.flows.keys()
    flows_list.sort()
    click.echo()
    click.echo('# Flows')
    click.echo('What CumulusCI flows should this plan run?  You can enter multiple flows using a comma as a separator')
    click.echo('Available Flows: {}'.format(', '.join(flows_list)))
    flows = click.prompt('Flow(s)')

    click.echo()
    click.echo('# Trigger Type')
    click.echo('How should this plan be triggered?')
    click.echo('  - commit: Trigger on branch commits matching a regex pattern')
    click.echo('  - tag: Trigger on new tags matching a regex pattern')
    click.echo('  - manual: Do not auto-trigger any builds.  Can be manually triggered.')
    trigger_type = click.prompt('Trigger Type (commit, tag, or manual)')
    if trigger_type == 'commit':
        regex = click.prompt('Branch Match RegEx (ex feature/.*)')
    elif trigger_type == 'tag':
        regex = click.prompt('Tag Match RegEx (ex beta/.*)')
    elif trigger_type != 'manual':
        raise click.UsageError('{} is an invalid trigger type.  Valid choices are: commit, tag, manual')
    else:
        regex = None

    click.echo()
    click.echo('# Github Commit Status')
    click.echo('MetaCI can set the build status via the Github Commit Status API.  Commit statuses are grouped by a context field.  Setting a different context on different plans will cause multiple commit statuses to be created for each unique context in Github.')
    context = None
    if click.confirm('Set commit status in Github for this plan?', default=True):
        context = click.prompt('Github Commit Status Context', default=name)

    if trigger_type == 'manual':
        active = True
    else:
        click.echo()
        click.echo('# Activate Plan')
        match_str = 'matching regex {}'.format(regex) if regex else ''
        click.echo('If active, this plan will automatically build on new {}s{}'.format(trigger_type, match_str))
        active = click.confirm('Active?', default=True)
    
    click.echo()
    click.echo('# Public or Private')
    click.echo('Public plans and their builds are visible to anonymous users.  This is recommended for open source projects, instances on an internal network or VPN, or projects that want transparency of their build information.  Private plans are only visible to logged in users who have been granted the Is Staff role by an admin.')
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
    }

    res = api_client('plans', 'create', params=params)

    click.echo()
    click.echo(
        click.style(
            'Created plan {} with the following configuration'.format(name),
            fg='green',
        )
    )
    render_recursive(res)

    click.echo()
    click.echo('Adding repository {owner}/{name} to plan'.format(**repo_data))

    params = {
        'repo_id': repo_data['id'],
        'plan_id': res['id'],
    }
    res = api_client('plan_repos', 'create', params=params)

@click.command(name='info', help='Show info for a plan')
@click.argument('plan_id')
@pass_config
def plan_info(config, plan_id):
    api_client = ApiClient(config)
    plan = get_plan(api_client, plan_id)
    click.echo(render_recursive(plan))


@click.command(name='list', help='Lists plans')
@pass_config
def plan_list(config):
    api_client = ApiClient(config)

    res = api_client('plans', 'list')

    plan_list_fmt = '{id:<5} {name:24.24} {org:12.12} {flows:24.24} {type:7.7} {regex}'
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

@click.command(name='repo_add', help='Add a repo to a plan')
@click.argument('plan_id')
@click.option('--repo', help='Specify the repo in format OwnerName/RepoName')
@pass_config
def plan_repo_add(config, plan_id, repo):
    api_client = ApiClient(config)

    # Look up the plan
    plan = get_plan(api_client, plan_id)

    # Filter by repository
    repo_data = lookup_repo(api_client, config, repo, required=True)

    # Check that we don't already have a matching PlanRepository
    params = {
        'plan': plan_id,
        'repo': repo_data['id'],
    }
    res = api_client('plan_repos', 'list', params=params)
    if res['count']:
        raise click.ClickException('Repo already added to plan')

    # Create the PlanRepository
    params = {
        'plan_id': plan_id,
        'repo_id': repo_data['id'],
    }
    res = api_client('plan_repos', 'create', params=params)
    click.echo()
    click.echo('Added repo {repo[owner]}/{repo[name]} to plan {plan[name]}'.format(**res))
    render_recursive(res)

@click.command(name='repo_list', help='List repos associated with a plan')
@click.argument('plan_id')
@pass_config
def plan_repo_list(config, plan_id):
    api_client = ApiClient(config)
    plan = get_plan(api_client, plan_id)
    params = {
        'plan': plan_id,
    }
    res = api_client('plan_repos', 'list', params=params)
    click.echo()
    click.echo('Repos associated with plan {}:')
    repo_list_fmt = '{id:<5} {repo[id]:<6} {repo[name]:32.32} {repo[owner]}'
    headers = {
        'id': '#',
        'repo': {
            'id': 'Repo #',
            'name': 'Name',
            'owner': 'Owner',
        },
    }
    click.echo(repo_list_fmt.format(**headers))
    for plan_repo in res['results']:
        click.echo(repo_list_fmt.format(**plan_repo))

@click.command(name='run', help='Run a plan')
@click.argument('plan_id')
@click.option('--branch', help="Specify a branch other than the current local branch")
@click.option('--commit', help="Specify a remote Github commit sha to build instead of the branch HEAD")
#@click.option('--keep-org', is_flag=True, help="If set, plans that generate scratch orgs will not delete the org.  This is useful for manual testing and debugging.  Use metaci build org_login <build_id> to log into the org once it is created.")
@pass_config
def plan_run(config, plan_id, branch, commit):
    api_client = ApiClient(config)
    plan = get_plan(api_client, plan_id)
    
    # Look up the repo
    repo_data = lookup_repo(api_client, config, None, required=True)

    # Look up the plan org
    org_params = {
        'repo': repo_data['id'],
        'name': plan['org'],
    }
    org_res = api_client('orgs', 'list', params=org_params)
    if org_res['count'] == 0:
        raise click.ClickException('The plan org "{}" does not exist in MetaCI.  Use metaci org create to create the org.'.format(plan['org']))
    org_data = org_res['results'][0]

    # Look up the branch
    if not branch:
        branch = config.project_config.repo_branch
    branch_data = get_or_create_branch(api_client, branch, repo_data['id'])

    # Determine the commit
    if not commit:
        gh = config.project_config.get_github_api()
        gh_repo = gh.repository(
            config.project_config.repo_owner,
            config.project_config.repo_name,
        )
        branch = gh_repo.branch(branch)
        commit = branch.commit.sha

    # Create the build
    build_params = {
        'repo_id': repo_data['id'],
        'org_id': org_data['id'],
        'plan_id': plan_id,
        'branch_id': branch_data['id'],
        'commit': commit,
    }
    resp = api_client('builds', 'create', params=build_params)
    click.echo(click.style('Build {} created successfully'.format(resp['id']), bold=True, fg='green'))
    click.echo('Use metaci build info {} to monitor the build or metaci build list to monitor multiple builds'.format(resp['id']))


plan.add_command(plan_add)
plan.add_command(plan_browser)
plan.add_command(plan_info)
plan.add_command(plan_list)
plan.add_command(plan_repo_add)
plan.add_command(plan_repo_list)
plan.add_command(plan_run)
main.add_command(plan)
