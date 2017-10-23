import click
from coreapi import Client
from coreapi.transports import HTTPTransport
from cumulusci.core.exceptions import ServiceNotConfigured

class ApiClient(object):
    def __init__(self, config):
        headers = {}
        try:
            service = config.keychain.get_service('metaci')            
            headers['Authorization'] = 'Token {}'.format(service.token)
        except ServiceNotConfigured:
            raise click.ClickException('You must have a MetaCI site configured.  Use metaci site connect to configure an existing site or metaci site create to deploy a new Heroku app running MetaCI.')
            
        self.client = Client(transports=[
            HTTPTransport(headers=headers),
        ])
        self._load_document()

    def _load_document(self):
        self.document = self.client.get('http://localhost:8000/api/schema')
    
    def __call__(self, *args, **kwargs):
        """ A shortcut to allow api_client('action') instead of api_client.client.action(self.document, 'action') """
        return self.client.action(self.document, args, **kwargs)
