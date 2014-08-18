from functools import wraps
import random
import time

from openstack_plugin_common import OpenStackClient
from openstack_plugin_common import KeystoneConfig
from openstack_plugin_common import KeystoneClient
from heatclient.v1.client import Client as heat_Client
import neutronclient.v2_0.client as neutron_client
import neutronclient.common.exceptions as neutron_exceptions
import novaclient.v1_1.client as nova_client
import novaclient.exceptions as nova_exceptions
import cloudify.manager
import cloudify.decorators
from cloudify_rest_client.exceptions import CloudifyClientError
from cloudify_rest_client.nodes import Node
from cloudify_rest_client import CloudifyClient


CLEANUP_RETRIES = 10
CLEANUP_RETRY_SLEEP = 2
NOVA_SERVER_TYPE = 'OS::Nova::Server'
NEUTRON_NETWORK_TYPE = 'network'
NEUTRON_FLOATINGIP_TYPE = 'floatingip'
NEUTRON_PORT_TYPE = 'port'
NEUTRON_ROUTER_TYPE = 'router'
NEUTRON_SECURITY_GROUP_TYPE = 'security_group'
NEUTRON_SUBNET_TYPE = 'subnet'


class HeatNovaClient(OpenStackClient):
    config = KeystoneConfig

    def connect(self, cfg):
        self.stack_name = cfg.get('stack_name')
        self.template_url = cfg.get('template_url')

        ks = KeystoneClient().get(config=cfg.get('keystone_config'))
        heat_endpoint = \
            ks.service_catalog.url_for(service_type='orchestration',
                                                    endpoint_type='publicURL')
        nova = nova_client.Client(username=cfg['username'],
                                  api_key=cfg['password'],
                                  project_id=cfg['tenant_name'],
                                  auth_url=cfg['auth_url'],
                                  region_name=cfg['region'],
                                  http_log_debug=False)
        ret = HeatNovaClientWithSugar(heat_endpoint,
                                      stack_name=self.stack_name,
                                      template_url=self.template_url,
                                      nova_client=nova,
                                      token=ks.auth_token)
        ret.format = 'json'
        return ret


class HeatNeutronClient(OpenStackClient):
    config = KeystoneConfig

    def connect(self, cfg):
        self.stack_name = cfg.get('stack_name')
        self.template_url = cfg.get('template_url')

        ks = KeystoneClient().get(config=cfg.get('keystone_config'))
        neutron_endpoint = \
            ks.service_catalog.url_for(service_type='network',
                                        endpoint_type='publicURL')
        heat_endpoint = \
            ks.service_catalog.url_for(service_type='orchestration',
                                                    endpoint_type='publicURL')
        neutron = neutron_client.Client(endpoint_url=neutron_endpoint,
                                     token=ks.auth_token)
        ret = HeatNeutronClientWithSugar(heat_endpoint,
                                      stack_name=self.stack_name,
                                      template_url=self.template_url,
                                      neutron_client=neutron,
                                      token=ks.auth_token)
        ret.format = 'json'
        return ret

# Decorators


def _find_instanceof_in_kw(cls, kw):
    ret = [v for v in kw.values() if isinstance(v, cls)]
    if not ret:
        return None
    if len(ret) > 1:
        raise NonRecoverableError(
            "Expected to find exactly one instance of {0} in "
            "kwargs but found {1}".format(cls, len(ret)))
    return ret[0]


def _find_context_in_kw(kw):
    return _find_instanceof_in_kw(cloudify.context.CloudifyContext, kw)



def with_heat_neutron_client(f):
    @wraps(f)
    def wrapper(*args, **kw):
        ctx = _find_context_in_kw(kw)
        if ctx:
#            ls = [caps for caps in ctx.capabilities.get_all().keys() if
#                   'heat_stack' in caps]
#            if len(ls) != 1:
#                raise RuntimeError('Expected exactly one heat stack. got'
#                                  ' {0}'.format(ls))
            restclient = CloudifyClient('127.0.0.1')
            nodes = restclient.nodes.list(ctx.deployment_id)
            ls = [node for node in nodes if node.id == 'heat_stack']
            if len(ls) != 1:
                raise RuntimeError('Expected exactly one heat stack. got')
            nodeprops = ls[0].properties
            cfg = {}
            cfg['stack_name'] = nodeprops['stack_name']
            cfg['template_url'] = nodeprops['template_url']
#            ctx.properties['management_network_name'] = nodeprops['management_network_name']
            logger = ctx.logger
        else:
            raise RuntimeError(
                "Expected to find context ")
        heat_client = ExceptionRetryProxy(
            HeatNeutronClient().get(config=cfg),
            exception_handler=neutron_exception_handler,
            logger=logger)
        kw['heat_neutron_client'] = heat_client
        return f(*args, **kw)
    return wrapper

def with_heat_nova_client(f):
    @wraps(f)
    def wrapper(*args, **kw):
        ctx = _find_context_in_kw(kw)
        if ctx:
#            ls = [caps for caps in ctx.capabilities.get_all().keys() if
#                  'heat_stack' in caps]
#            if len(ls) != 1:
#                raise RuntimeError('Expected exactly one heat stack. got'
#                                   ' {0}'.format(ls))
            restclient = CloudifyClient('127.0.0.1')
            nodes = restclient.nodes.list(ctx.deployment_id)
            ls = [node for node in nodes if node.id == 'heat_stack']
            if len(ls) != 1:
                raise RuntimeError('Expected exactly one heat stack. got')
            nodeprops = ls[0].properties
            cfg = {}
            cfg['stack_name'] = nodeprops['stack_name']
            cfg['template_url'] = nodeprops['template_url']
#            ctx.properties['management_network_name'] = nodeprops['management_network_name']
            logger = ctx.logger
        else:
            raise RuntimeError(
                "Expected to find context ")

        heat_client = ExceptionRetryProxy(
            HeatNovaClient().get(config=cfg),
            exception_handler=_nova_exception_handler,
            logger=logger)
        kw['heat_nova_client'] = heat_client
        return f(*args, **kw)
    return wrapper


def _nova_exception_handler(exception):
    if not isinstance(exception, nova_exceptions.OverLimit):
        raise
    retry_after = exception.retry_after
    if retry_after == 0:
        retry_after = 5
    return retry_after

def neutron_exception_handler(exception):
    if not isinstance(exception, neutron_exceptions.NeutronClientException):
        raise
    if exception.message is not None and \
            'TokenRateLimit' not in exception.message:
        raise
    retry_after = 30
    return retry_after

class HeatNovaClientWithSugar(heat_Client):
    """Initiate an Heat Client with stack name and template url"""
    def __init__(self, endpoint, nova_client, stack_name=None, template_url=None, *args, **kwargs):
        super(HeatNovaClientWithSugar, self).__init__(endpoint, *args, **kwargs)
        self.stack_name = stack_name
        self.template_url = template_url
        self.nova_client = nova_client
    

    def cosmo_get(self, resource_name):
        res = self.resources.get(self.stack_name, resource_name)
        phys_id = res.physical_resource_id
        res_type = res.resource_type
        if NOVA_SERVER_TYPE not in res_type:
            raise RuntimeError('Heat resource type is {0}, expecting {1}'
                               .format(res_type, NOVA_SERVER_TYPE))

        return self.nova_client.servers.get(phys_id)

    def get(self, phys_id):
        return self.nova_client.servers.get(phys_id);

    def list(self):
        return self.nova_client.servers.list()

    def set_meta(self, server, metadata):
        self.nova_client.servers.set_meta(server, metadata)


class HeatNeutronClientWithSugar(heat_Client):
    """Initiate an Heat Client with stack name and template url"""
    def __init__(self, endpoint, neutron_client, stack_name=None, template_url=None, *args, **kwargs):
        super(HeatNeutronClientWithSugar, self).__init__(endpoint, *args, **kwargs)
        self.stack_name = stack_name
        self.template_url = template_url
        self.neutron_client = neutron_client

    def cosmo_get_named(self, obj_type_single, name, **kw):
        return self.cosmo_get(obj_type_single, name=name, **kw)

    def cosmo_get(self, external_type, resource_name):
        res = self.resources.get(self.stack_name, resource_name)
        phys_id = res.physical_resource_id
#        res_type = res.resource_type
        show_neutron_for_type = getattr(self.neutron_client, 'show_' + external_type)
        return show_neutron_for_type(phys_id) 


class ExceptionRetryProxy(object):

    def __init__(self, delegate, exception_handler, logger=None):
        self.delegate = delegate
        self.logger = logger
        self.exception_handler = exception_handler

    def __getattr__(self, name):
        attr = getattr(self.delegate, name)
        if callable(attr):
            def wrapper(*args, **kwargs):
                retries = 5
                for i in range(retries):
                    try:
                        return attr(*args, **kwargs)
                    except Exception, e:
                        if i == retries - 1:
                            break
                        retry_after = self.exception_handler(e)
                        retry_after += random.randint(0, retry_after)
                        if self.logger is not None:
                            message = '{0} exception caught while ' \
                                      'executing {1}. sleeping for {2} ' \
                                      'seconds before trying again (Attempt' \
                                      ' {3}/{4})'.format(type(e),
                                                         name,
                                                         retry_after,
                                                         i+2,
                                                         retries)
                            self.logger.warn(message)
                        time.sleep(retry_after)
                raise
            return wrapper
        return attr
