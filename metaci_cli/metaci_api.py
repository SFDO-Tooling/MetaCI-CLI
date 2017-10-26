import click
from requests.exceptions import ConnectionError
import coreapi
from cumulusci.core.exceptions import ServiceNotConfigured

class ApiClient(object):
    def __init__(self, config):
        headers = {}
        try:
            self.service = config.keychain.get_service('metaci')            
        except ServiceNotConfigured:
            raise click.ClickException('You must have a MetaCI site configured.  Use metaci site connect to configure an existing site or metaci site create to deploy a new Heroku app running MetaCI.')
           
        auth = coreapi.auth.TokenAuthentication(self.service.token, scheme='Token')
        self.client = coreapi.Client(auth=auth)
        self._load_document()

    def _load_document(self):
        try:
            self.document = self.client.get(self.service.url + '/api/schema')
        except ConnectionError as e:
            self._handle_connection_error(e)
    
    def __call__(self, *args, **kwargs):
        """ A shortcut to allow api_client('action') instead of api_client.client.action(self.document, 'action') """
        try:
            resp = self.client.action(self.document, args, **kwargs)
        except ConnectionError as e:
            self.handle_connection_error(e)
        return resp

    def _handle_connection_error(self, e):
        raise click.ClickException('Could not connect to MetaCI site.  Try metaci site browser to open the site in a browser')

