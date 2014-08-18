
from cloudify.decorators import operation
from heat_plugin_common import with_heat_nova_client
from heat_plugin_common import NOVA_SERVER_TYPE


NODE_ID_PROPERTY = 'cloudify_id'
OPENSTACK_SERVER_ID_PROPERTY = 'openstack_server_id'


@operation
@with_heat_nova_client
def start(ctx, heat_nova_client, **kwargs):
    server = get_server_by_context(heat_nova_client, ctx)
    if server is not None:
        ctx.runtime_properties['openstack_server_id'] = server.id
#        ctx.properties['image_name']= server.image['id']
#        ctx.properties['flavor_id']= server.flavor['id']
#        ctx.properties['key_name']= server.key_name
#        ctx.properties['external_type'] = NOVA_SERVER_TYPE
        ctx.runtime_properties.update(server.to_dict())
        ctx['enable_deletion'] = False  # Not acquired herea
        metadata = dict({})
        metadata['cloudify_id']= ctx.node_id
        metadata['cloudify_management_network_name']= ctx.properties['cloudify_management_network_name']
        heat_nova_client.set_meta(server, metadata)


        return


@operation
@with_heat_nova_client
def stop(ctx, heat_nova_client, **kwargs):
    """
    No Op stub because Heat will stop the server.
    """


@operation
@with_heat_nova_client
def delete(ctx, heat_nova_client, **kwargs):
    """
    No Op stub because Heat will delete the server.
    """


def get_server_by_context(heat_nova_client, ctx):
    """
    Gets a server for the provided context.

    If openstack server id is present it would be used for getting the server.
    Otherwise, an iteration on all servers metadata will be made.
    """
    # ls = [caps for caps in ctx.capabilities.get_all().values() if
    #       caps.get('external_type') == 'heat_stack']
    # if len(ls) != 1:
    #     raise RuntimeError('Expected exactly one heat stack. got'
    #                        ' {0}'.format(ls))
    # heat_stack = ls[0]
    openstack_server_id = None
    if 'openstack_server_id' in ctx.runtime_properties:
        openstack_server_id = ctx.runtime_properties['openstack_server_id']
    elif 'openstack_server_id' in ctx.properties['server']:
        openstack_server_id = ctx.properties['server']['openstack_server_id']
    if openstack_server_id:
        ctx.logger.info("get_server_by_context trying to get server for openstack_server_id: {0}".format(
            openstack_server_id))
        try:
            return heat_nova_client.get(
                openstack_server_id)
        except nova_exceptions.NotFound:
            return None
    # Fallback
    servers = heat_nova_client.list()
    for server in servers:
       if 'cloudify_id' in server.metadata and \
                ctx.node_id == server.metadata['cloudify_id']:
            return server
    ctx.logger.info("get_server_by_context could not find server with cloudify_id")
    return None


@operation
@with_heat_nova_client
def get_state(ctx, heat_nova_client, **kwargs):
    server = get_server_by_context(heat_nova_client, ctx)
    if server.status == 'ACTIVE':
        ips = {}
        _, default_network_ips = server.networks.items()[0]
        manager_network_ip = None
        management_network_name = server.metadata.get(
            'cloudify_management_network_name')
        for network, network_ips in server.networks.items():
            if management_network_name and network == management_network_name:
                manager_network_ip = network_ips[0]
            ips[network] = network_ips
        if manager_network_ip is None:
            manager_network_ip = default_network_ips[0]
        ctx.runtime_properties['networks'] = ips
        # The ip of this instance in the management network
        ctx.runtime_properties['ip'] = manager_network_ip
        return True
    return False


def _fail_on_missing_required_parameters(obj,
                                         required_parameters, hint_where):
    for k in required_parameters:
        if k not in obj:
            raise ValueError(
                "Required parameter '{0}' is missing (under host's "
                "properties.{1}). Required parameters are: {2}"
                .format(k, hint_where, required_parameters))


@operation
def connect_floatingip(ctx, **kwargs):
    ctx.logger.info("Floatingip {0} was added to server {1}".format(
        ctx.related.runtime_properties['floating_ip_address'],
        ctx.runtime_properties['openstack_server_id'])
    )


@operation
def disconnect_floatingip(ctx, **kwargs):
     ctx.logger.debug("Floatingip {0} is asked to be removed from server {1}"
        .format(ctx.related.runtime_properties['floating_ip_address'],
        ctx.runtime_properties['openstack_server_id'])
    )

@operation
def disconnect_subnet(ctx, **kwargs):
    ctx.logger.debug("Subnet {0} is asked to be disconnected from router {1}"
        .format(ctx.related.runtime_properties['external_id'],
        ctx.runtime_properties['openstack_server_id'])
    )
