from cloudify.decorators import operation
from heat_plugin_common import with_heat_neutron_client
from heat_plugin_common import NEUTRON_PORT_TYPE


@operation
@with_heat_neutron_client
def create(ctx, heat_neutron_client, **kwargs):

   # Already discovered?
    port = heat_neutron_client.cosmo_get('port', ctx.node_name)
    if port is None:
        raise RuntimeError('Cloud not find port {0} '.format(ctx.node_name))
    ctx.runtime_properties['external_id'] = port[NEUTRON_PORT_TYPE]['id']
#    ctx['external_type'] = NEUTRON_PORT_TYPE
#    ctx.runtime_properties.update(port[NEUTRON_PORT_TYPE])
    ctx['enable_deletion'] = False  # Not acquired here
    return


@operation
@with_heat_neutron_client
def delete(ctx, heat_neutron_client, **kwargs):
    do_delete = bool(ctx.runtime_properties.get('enable_deletion'))
    op = ['Not deleting', 'Deleting'][do_delete]
    ctx.logger.debug("{0} port {1}".format(
        op, ctx.node_name)
#    neutron_client.delete_port(ctx.runtime_properties['external_id'])
    )

@operation
@with_heat_neutron_client
def connect_security_group(ctx, heat_neutron_client, **kwargs):
    # WARNING: non-atomic operation
    ctx.logger.info(
        "connect_security_group(): id={0} related={1}".format(
            ctx.runtime_properties['external_id'],
            ctx.related.runtime_properties)
    )
