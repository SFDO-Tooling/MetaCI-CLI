import os
import sys
import time

try:
    import anydbm as dbm
except ImportError:
    import dbm

import click
import pkg_resources
import requests

from cumulusci.core.config import YamlGlobalConfig
from cumulusci.core.config import YamlProjectConfig
from cumulusci.core.exceptions import NotInProject
from cumulusci.core.exceptions import ProjectConfigNotFound
from cumulusci.core.utils import import_class


def dbm_cache():
    """
    context manager for accessing simple dbm cache
    located at ~/.cumlusci/cache.dbm
    """
    config_dir = os.path.join(
        os.path.expanduser('~'),
        YamlGlobalConfig.config_local_dir,
    )
        
    if not os.path.exists(config_dir):
        os.mkdir(config_dir)

    db = dbm.open(os.path.join(config_dir, 'cache.dbm'), 'c',)
    yield db
    db.close()


def get_installed_version():
    """ returns the version name (e.g. 2.0.0b58) that is installed """
    req = pkg_resources.Requirement.parse('metaci_cli')
    dist = pkg_resources.WorkingSet().find(req)
    return pkg_resources.parse_version(dist.version)


def get_latest_version():
    """ return the latest version of metaci_cli in pypi, be defensive """
    # use the pypi json api https://wiki.python.org/moin/PyPIJSON
    res = requests.get('https://pypi.python.org/pypi/metaci_cli/json', timeout=5).json()
    with dbm_cache() as cache:
        cache['metaci_cli-latest-timestamp'] = str(time.time())
    return pkg_resources.parse_version(res['info']['version'])


def check_latest_version():
    """ checks for the latest version of metaci_cli from pypi, max once per hour """
    check = True

    with dbm_cache() as cache:
        if cache.has_key('metaci_cli-latest-timestamp'):
            delta = time.time() - float(cache['metaci_cli-latest-timestamp'])
            check = delta > 3600

    if check:
        result = get_latest_version() > get_installed_version()
        click.echo('Checking the version!')
        if result:
            click.echo(
                "An update to CumulusCI is available. Use pip install --upgrade metaci_cli to update.")

# From https://stackoverflow.com/a/3681323
def get_dict_attr(obj, attr):
    for obj in [obj] + obj.__class__.mro():
        if attr in obj.__dict__:
            return obj.__dict__[attr]
    raise AttributeError

 
class CliConfig(object):

    @property
    def global_config(self):
        if not hasattr(self, '_global_config'):
            self._load_global_config()
        return self._global_config
        
    def _load_global_config(self):
        try:
            self._global_config = YamlGlobalConfig()
        except NotInProject as e:
            raise click.ClickException(e.message)

    @property
    def project_config(self):
        if not hasattr(self, '_project_config'):
            self._load_project_config()
        return self._project_config
        
    def _load_project_config(self):
        try:
            self._project_config = self.global_config.get_project_config()
        except ProjectConfigNotFound:
            self._project_config = None
        except NotInProject as e:
            raise click.ClickException(e.message)
        except ConfigError as e:
            raise click.ClickException('Config Error: {}'.format(e.message))

        # Set the keychain to lazy mode on the project so the first reference
        # to self.keychain doesn't actually initialize the keychain but 
        # subsequent calls will
        self._project_config.keychain = get_dict_attr(self, 'keychain')

    @property
    def keychain(self):
        if not hasattr(self, '_keychain'):
            self._load_keychain()
        return self._keychain

    def _load_keychain(self):
        self.keychain_key = os.environ.get('CUMULUSCI_KEY')
        if self.project_config:
            keychain_class = os.environ.get(
                'CUMULUSCI_KEYCHAIN_CLASS',
                self.project_config.cumulusci__keychain,
            )
            self.keychain_class = import_class(keychain_class)
            self._keychain = self.keychain_class(
                self.project_config, self.keychain_key)
            self.project_config.set_keychain(self.keychain)

def make_pass_instance_decorator(obj, ensure=False):
    """Given an object type this creates a decorator that will work
    similar to :func:`pass_obj` but instead of passing the object of the
    current context, it will inject the passed object instance.

    This generates a decorator that works roughly like this::
        from functools import update_wrapper
        def decorator(f):
            @pass_context
            def new_func(ctx, *args, **kwargs):
                return ctx.invoke(f, obj, *args, **kwargs)
            return update_wrapper(new_func, f)
        return decorator
    :param obj: the object instance to pass.
    """
    def decorator(f):
        def new_func(*args, **kwargs):
            ctx = click.get_current_context()
            return ctx.invoke(f, obj, *args[1:], **kwargs)
        return click.decorators.update_wrapper(new_func, f)
    return decorator

try:
    CLI_CONFIG = CliConfig()
except click.UsageError as e:
    click.echo(e.message)
    sys.exit(1)

pass_config = make_pass_instance_decorator(CLI_CONFIG)
