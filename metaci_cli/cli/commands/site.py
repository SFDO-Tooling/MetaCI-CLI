# -*- coding: utf-8 -*-

"""Console script for metaci_cli."""

import click
import json
import requests
import time
import webbrowser
from cumulusci.core.config import ServiceConfig
from cumulusci.core.exceptions import ServiceNotConfigured
from metaci_cli.cli.commands.main import main
from metaci_cli.cli.util import render_recursive
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

app_shape_choice = click.Choice(['dev','staging','prod'])

@click.command(name='create', help='Deploy a new Heroku app running MetaCI')
@click.option('--name', help='Specify an app name instead of prompting for it')
@click.option('--shape', 
    help='Specify an app shape instead of prompting for it', 
    type=app_shape_choice,
)
@pass_config
def site_create(config, name, shape):
    if not config.project_config:
        raise click.ClickException('You must be in a CumulusCI configured local git repository.')
   
    verify_overwrite(config)

    # Initialize payload
    payload = {
        'app': {},
        'source_blob': {
            'url': 'https://github.com/SalesforceFoundation/mrbelvedereci/tarball/feature/api/',
        },
    }
    env = {} 

    # Heroku API Token
    click.echo()
    click.echo(click.style('# Heroku API Token', bold=True))
    click.echo('Enter your Heroku API Token.  If you do not have a token, go to the Account page in Heroku and use the API Token section: https://dashboard.heroku.com/account')
    click.echo(click.style(
        'NOTE: For security purposes, your input will be hidden.  Paste your API Token and hit Enter to continue.',
        fg='yellow',
    ))
    token = click.prompt('API Token', hide_input=True)

    # App Name
    if not name:
        click.echo()
        click.echo(click.style('# Heroku App Name'))
        click.echo('Specify the name of the Heroku app you want to create.')
        payload['app']['name'] = click.prompt('App Name')
    else:
        payload['app']['name'] = name

    # App Shape
    if not shape:
        click.echo()
        click.echo(click.style('# Heroku App Shape'))
        click.echo('Select the Heroku app shape you want to deploy.  Available options:')
        click.echo('  - dev: Runs on free Heroku resources with build concurrency of 1')
        click.echo('  - staging: Runs on paid Heroku resources with fixed build concurrency of X')
        click.echo('  - prod: Runs on paid Heroku resources auto-scaled build concurrency via Hirefire.io (paid add on configured separately)')
        app_shape = click.prompt('App Shape', type=app_shape_choice)

    # Salesforce DX
    click.echo()
    click.echo(click.style('# Salesforce DX Configuration'))
    click.echo('The following prompts collect information from your local Salesforce DX configuration to use to configure MetaCI to use sfdx')
    # Salesforce DX Hub Key
    click.echo()
    click.echo('MetaCI uses JWT to connect to your Salesforce DX devhub.  Please enter the path to your local private key file.  If you have not set up JWT for your devhub, refer to the documentation: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_jwt_flow.htm')
    sfdx_private_key = click.prompt('Path to private key', type=click.File())
    env['SFDX_HUB_KEY'] = sfdx_private_key.read()
    # Salesforce DX Client ID
    click.echo()
    click.echo('Enter the Connected App Client ID you used for the JWT authentication flow to the Salesforce DX devhub.')
    click.echo(click.style(
        'NOTE: For security purposes, your input will be hidden.  Paste your Client ID and hit Enter to continue.',
        fg='yellow',
    ))
    env['SFDX_CLIENT_ID'] = click.prompt('Client ID', hide_input=True)
    # Salesforce DX Username
    click.echo()
    click.echo('Enter the username MetaCI should use for JWT authentication to the Salesforce DX devhub.')
    env['SFDX_HUB_USERNAME'] = click.prompt('Username')

    # Get connected app info from CumulusCI keychain
    connected_app = config.keychain.get_connected_app()
    env['CONNECTED_APP_CALLBACK_URL'] = connected_app.callback_url
    env['CONNECTED_APP_CLIENT_ID'] = connected_app.client_id
    env['CONNECTED_APP_CLIENT_SECRET'] = connected_app.client_secret

    # Set the site url
    env['SITE_URL'] = 'https://{}.herokuapp.com'.format(payload['app']['name'])

    # Get Github credentials from CumulusCI keychain
    github = config.keychain.get_service('github')
    env['GITHUB_USERNAME'] = github.username
    env['GITHUB_PASSWORD'] = github.password
    env['GITHUB_WEBHOOK_BASE_URL'] = '{SITE_URL}/webhook/github'.format(**env)
    env['FROM_EMAIL'] = github.email

    # Prepare the payload 
    payload['overrides'] = {
        'env': env,
    } 

    # Create the new Heroku App
    headers = {
        'Accept': 'application/vnd.heroku+json; version=3',
        'Authorization': 'Bearer {}'.format(token),
    }
    resp = requests.post('https://api.heroku.com/app-setups', json=payload, headers=headers)
    if resp.status_code != 202:
        raise click.ClickException('Failed to create Heroku App.  Reponse code [{}]: {}'.format(resp.status_code, resp.json()))
    app_setup = resp.json()
    
    # Check status
    status = app_setup['status']
    click.echo()
    click.echo('Status: {}'.format(status))
    i = 1
    with click.progressbar(length=100) as bar:
        while status in ['pending']:
            check_resp = requests.get(
                'https://api.heroku.com/app-setups/{id}'.format(**app_setup),
                headers=headers,
            )
            if check_resp.status_code != 200:
                raise click.ClickException('Failed to check status of app creation.  Reponse code [{}]: {}'.format(check_resp.status_code, check_resp.json()))
            check_data = check_resp.json()
            if check_data['status'] != 'pending':
                break
            i += 1
            bar.update(i)
            time.sleep(2)

    click.echo()
    # Success
    if check_data['status'] == 'succeeded':
        click.echo(click.style('Heroku app creation succeeded!', fg='green'))
        render_recursive(check_data)
    # Failed
    elif check_data['status'] == 'failed':
        click.echo(click.style('Heroku app creation failed', fg='red'))
        render_recursive(check_data)
        return
    else:
        raise click.ClickException('Received an unknown status from the Heroku app-setups API.  Full API response: {}'.format(check_data))

    # Apply the app shape
    if app_shape == 'staging':
        pass
    elif app_shape == 'prod':
        pass

    # Create a superuser
    
    # Set up the github service
    

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
    render_recursive(service.config)


site.add_command(site_browser)
site.add_command(site_create)
site.add_command(site_connect)
site.add_command(site_info)
main.add_command(site)
