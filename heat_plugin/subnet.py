from cloudify.decorators import operation
from heat_plugin_common import with_heat_neutron_client
from heat_plugin_common import NEUTRON_SUBNET_TYPE


@operation
@with_heat_neutron_client
def create(ctx, heat_neutron_client, **kwargs):
 
    subnet = heat_neutron_client.cosmo_get('subnet', ctx.node_name)
    if subnet is None:
        raise RuntimeError('Cloud not find subnet {0} '.format(ctx.node_name))
    ctx.runtime_properties['external_id'] = subnet[NEUTRON_SUBNET_TYPE]['id']
#    ctx.runtime_properties['external_type'] = NEUTRON_SUBNET_TYPE
#    ctx.runtime_properties.update(subnet[NEUTRON_SUBNET_TYPE])
    ctx['enable_deletion'] = False  # Not acquired here
    return


@operation
@with_heat_neutron_client
def delete(ctx, heat_neutron_client, **kwargs):
    do_delete = bool(ctx.runtime_properties.get('enable_deletion'))
    op = ['Not deleting', 'Deleting'][do_delete]
    ctx.logger.debug("{0} subnet {1}".format(
        op, ctx.node_name))
#    neutron_client.delete_subnet(ctx.runtime_properties['external_id'])
