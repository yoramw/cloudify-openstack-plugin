from cloudify.decorators import operation
from heat_plugin_common import with_heat_neutron_client
from heat_plugin_common import NEUTRON_ROUTER_TYPE


@operation
@with_heat_neutron_client
def create(ctx, heat_neutron_client, **kwargs):

   # Already discovered?
    router = heat_neutron_client.cosmo_get('router', ctx.node_name)
    if router is None:
        raise RuntimeError('Cloud not find router {0} '.format(ctx.node_name))
    ctx['external_id'] = network[NEUTRON_ROUTER_TYPE]['id']
    ctx['external_type'] = NEUTRON_ROUTER_TYPE
    ctx.runtime_properties.update(router[NEUTRON_ROUTER_TYPE])
    ctx['enable_deletion'] = False  # Not acquired here
    return


@operation
def connect_subnet(ctx, **kwargs):
    ctx.logger.debug("Subnet {0} connected to router {1}".format(
        ctx.related.runtime_properties['external_id'], ctx.runtime_properties['external_id'])
    )


@operation
def disconnect_subnet(ctx, **kwargs):
    ctx.logger.debug("Subnet {0} is asked to be disconnected from router {1}"
        .format(ctx.related.runtime_properties['external_id'],
        ctx.runtime_properties['external_id'])
    )

@operation
@with_heat_neutron_client
def delete(ctx, heat_neutron_client, **kwargs):
    do_delete = bool(ctx.runtime_properties.get('enable_deletion'))
    op = ['Not deleting', 'Deleting'][do_delete]
    ctx.logger.debug("{0} router {1}".format(
        op, ctx.node_name)
#    neutron_client.delete_router(ctx.runtime_properties['external_id'])
    )