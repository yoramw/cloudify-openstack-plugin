from cloudify.decorators import operation
from heat_plugin_common import with_heat_neutron_client
from heat_plugin_common import NEUTRON_SECURITY_GROUP_TYPE


@operation
@with_heat_neutron_client
def create(ctx, heat_neutron_client, **kwargs):

   # Already discovered?
    security_group = heat_neutron_client.cosmo_get('security_group', ctx.node_name)
    if security_group is None:
        raise RuntimeError('Cloud not find security_group {0} '.format(ctx.node_name))
    ctx['external_id'] = network[NEUTRON_SECURITY_GROUP_TYPE]['id']
    ctx['external_type'] = NEUTRON_SECURITY_GROUP_TYPE
    ctx.runtime_properties.update(security_group[NEUTRON_SECURITY_GROUP_TYPE])
    ctx['enable_deletion'] = False  # Not acquired here
    return


@operation
@with_heat_neutron_client
def delete(ctx, heat_neutron_client, **kwargs):
    do_delete = bool(ctx.runtime_properties.get('enable_deletion'))
    op = ['Not deleting', 'Deleting'][do_delete]
    ctx.logger.debug("{0} security_group {1}".format(
        op, ctx.node_name))
#    neutron_client.delete_security_group(ctx.runtime_properties['external_id'])
