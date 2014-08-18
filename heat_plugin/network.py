from cloudify.decorators import operation
from heat_plugin_common import with_heat_neutron_client
from heat_plugin_common import NEUTRON_NETWORK_TYPE


@operation
@with_heat_neutron_client
def create(ctx, heat_neutron_client, **kwargs):

   # Already discovered?
    network = heat_neutron_client.cosmo_get('network', ctx.node_name)
    if network is None:
        raise RuntimeError('Cloud not find network {0} '.format(ctx.node_name))
    ctx.runtime_properties['external_id'] = network[NEUTRON_NETWORK_TYPE]['id']
    ctx.runtime_properties['external_type'] = NEUTRON_NETWORK_TYPE
#    ctx.runtime_properties.update(network[NEUTRON_NETWORK_TYPE])
    ctx['enable_deletion'] = False  # Not acquired here
    return


@operation
@with_heat_neutron_client
def start(ctx, heat_neutron_client, **kwargs):
    neutron_client.update_network(ctx.runtime_properties['external_id'], {
        'network': {
            'admin_state_up': True
        }
    })


@operation
@with_heat_neutron_client
def stop(ctx, heat_neutron_client, **kwargs):
    neutron_client.update_network(ctx.runtime_properties['external_id'], {
        'network': {
            'admin_state_up': False
        }
    })


@operation
@with_heat_neutron_client
def delete(ctx, heat_neutron_client, **kwargs):
    do_delete = bool(ctx.runtime_properties.get('enable_deletion'))
    op = ['Not deleting', 'Deleting'][do_delete]
    ctx.logger.debug("{0} network {1}".format(
        op, ctx.node_name))
#    neutron_client.delete_network(ctx.runtime_properties['external_id'])
