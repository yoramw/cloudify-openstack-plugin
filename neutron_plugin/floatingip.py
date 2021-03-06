#########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from openstack_plugin_common import with_neutron_client, provider


@operation
@with_neutron_client
def create(ctx, neutron_client, **kwargs):

    # Already acquired?
    if ctx.runtime_properties.get('external_id'):
        ctx.logger.debug("Using already allocated Floating IP {0}".format(
            ctx.runtime_properties['floating_ip_address']))
        return

    floatingip = {
        # No defaults
    }
    floatingip.update(ctx.properties['floatingip'])

    # Sugar: ip -> (copy as is) -> floating_ip_address
    if 'ip' in floatingip:
        floatingip['floating_ip_address'] = floatingip['ip']
        del floatingip['ip']

    if 'floating_ip_address' in floatingip:
        fip = neutron_client.cosmo_get(
            'floatingip',
            floating_ip_address=floatingip['floating_ip_address'])
        ctx.runtime_properties['external_id'] = fip['id']
        ctx.runtime_properties['floating_ip_address'] = \
            fip['floating_ip_address']
        ctx.runtime_properties['enable_deletion'] = False  # Not acquired here
        return

    # Sugar: floating_network_name -> (resolve) -> floating_network_id
    if 'floating_network_name' in floatingip:
        floatingip['floating_network_id'] = neutron_client.cosmo_get_named(
            'network', floatingip['floating_network_name'])['id']
        del floatingip['floating_network_name']
    elif 'floating_network_id' not in floatingip:
        provider_context = provider(ctx)
        ext_network = provider_context.ext_network
        if ext_network:
            floatingip['floating_network_id'] = ext_network['id']
    else:
        raise NonRecoverableError('Missing floating network id or name')

    fip = neutron_client.create_floatingip(
        {'floatingip': floatingip})['floatingip']
    ctx.runtime_properties['external_id'] = fip['id']
    ctx.runtime_properties['floating_ip_address'] = fip['floating_ip_address']
    # Acquired here -> OK to delete
    ctx.runtime_properties['enable_deletion'] = True
    ctx.logger.info(
        "Allocated floating IP {0}".format(fip['floating_ip_address']))


@operation
@with_neutron_client
def delete(ctx, neutron_client, **kwargs):
    do_delete = bool(ctx.runtime_properties.get('enable_deletion'))
    op = ['Not deleting', 'Deleting'][do_delete]
    ctx.logger.debug("{0} floating IP {1}".format(
        op, ctx.runtime_properties['floating_ip_address']))
    if do_delete:
        neutron_client.delete_floatingip(ctx.runtime_properties['external_id'])
