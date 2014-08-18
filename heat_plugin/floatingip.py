from cloudify.decorators import operation
from heat_plugin_common import with_heat_neutron_client
from heat_plugin_common import NEUTRON_FLOATINGIP_TYPE

@operation
@with_heat_neutron_client
def create(ctx, heat_neutron_client, **kwargs):
    # Already discovered?
    floatingip = heat_neutron_client.cosmo_get('floatingip',ctx.node_name)
    if floatingip is None:
    	raise RuntimeError('Cloud not find floatingip {0} '.format(ctx.node_name))
#    ctx['external_type'] = NEUTRON_FLOATINGIP_TYPE
    ctx.runtime_properties.update(floatingip[NEUTRON_FLOATINGIP_TYPE])
    ctx.runtime_properties['floating_ip_address'] = floatingip[NEUTRON_FLOATINGIP_TYPE]['floating_ip_address']
#    ctx['fixed_ip_address'] = floatingip[NEUTRON_FLOATINGIP_TYPE]['fixed_ip_address']
    ctx['enable_deletion'] = False  # Not acquired here
    ctx.runtime_properties['external_id'] = floatingip[NEUTRON_FLOATINGIP_TYPE]['id']

    ctx.logger.info("External_id: {0} floating IP: {1}".format(
        floatingip[NEUTRON_FLOATINGIP_TYPE]['id'],ctx.runtime_properties['floating_ip_address']))


@operation
@with_heat_neutron_client
def delete(ctx, heat_neutron_client, **kwargs):
    do_delete = bool(ctx.runtime_properties.get('enable_deletion'))
    op = ['Not deleting', 'Deleting'][do_delete]
    ctx.logger.info("{0} floating IP {1}".format(
        op, ctx.runtime_properties['floating_ip_address']))
#    if do_delete:
#       neutron_client.delete_floatingip(ctx.runtime_properties['external_id'])
