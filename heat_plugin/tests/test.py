import argparse
import time
import logging

from cloudify.context import ContextCapabilities
from cloudify.mocks import MockCloudifyContext

import heat_plugin.server as cfy_srv
import heat_plugin.floatingip as cfy_floatingip
import heat_plugin.network as cfy_network
import openstack_plugin_common as common

from heat_plugin import server

#tests_config = common.TestsConfig().get()

DELETE_WAIT_START = 1
DELETE_WAIT_FACTOR = 2
DELETE_WAIT_COUNT = 6


class OpenstackHeatTest(object):

    def setUp(self):
        # Careful!
        logger = logging.getLogger(__name__)
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logger
        self.logger.level = logging.DEBUG
        self.logger.debug("Cosmo test setUp() called")

    def test_server_start(self):
        name = 'mysql_instance'
        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            node_name=name,
            properties={
                'server': {
                    'name': name,
                },
                'management_network_name': 'net_name'
            },
            capabilities=ContextCapabilities({
            	'heat_stack': {
            		'name': 'wp',
            		'external_type': 'stack',
            		'template_url': '',
            		'management_network_name': 'app_network'
            		}
            	})
        )

        cfy_srv.start(ctx=ctx)
        self.logger.debug(ctx)


    def test_floatingip_create(self):
        name = 'apache_floatingip'
        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            node_name=name,
            properties={
                'floatingip': {
                    'name': name,
                },
                'management_network_name': 'net_name'
            },
            capabilities=ContextCapabilities({
            	'heat_stack': {
            		'name': 'wp',
            		'external_type': 'stack',
            		'template_url': '',
            		'management_network_name': 'app_network'
            		}
            	})
        )

        cfy_floatingip.create(ctx=ctx)
        self.logger.debug(ctx)


    def test_network_create(self):
        name = 'data_network'
        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            node_name=name,
            properties={
                'network': {
                    'name': name,
                },
                'management_network_name': 'net_name'
            },
            capabilities=ContextCapabilities({
            	'heat_stack': {
            		'name': 'wp',
            		'external_type': 'stack',
            		'template_url': '',
            		'management_network_name': 'app_network'
            		}
            	})
        )

        cfy_network.create(ctx=ctx)
        self.logger.debug(ctx)


if __name__ == '__main__':
    os = OpenstackHeatTest()
    os.setUp()
    os.test_server_start()
    os.test_floatingip_create()
    os.test_network_create()


