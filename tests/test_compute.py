# Built-in Imports
import os
import sys

# Cloudify Imports
from ecosystem_tests import (
    PasswordFilter,
    EcosystemTestBase,
    utils as eco_utils)
from cloudify.exceptions import NonRecoverableError

WORDPRESS = 'https://github.com/cloudify-incubator/' \
            'cloudify-kubernetes-plugin/archive/master.zip'
DIAMOND_WAGON = 'https://github.com/cloudify-cosmo/' \
                'cloudify-diamond-plugin/releases/' \
                'download/1.3.8/cloudify_diamond_plugin-' \
                '1.3.8-py27-none-linux_x86_64-centos-Core.wgn'
DIAMOND_YAML = 'https://github.com/cloudify-cosmo/' \
               'cloudify-diamond-plugin/releases/' \
               'download/1.3.8/plugin.yaml'
HOST_POOL_WAGON = 'https://github.com/cloudify-cosmo/' \
                  'cloudify-host-pool-plugin/releases/' \
                  'download/1.5/cloudify_host_pool_plugin-' \
                  '1.5-py27-none-linux_x86_64-centos-Core.wgn'
HOST_POOL_YAML = 'https://github.com/cloudify-cosmo/' \
                 'cloudify-host-pool-plugin/releases/' \
                 'download/1.5/plugin.yaml'


class TestComputeKubernetesBlueprint(EcosystemTestBase):

    def setUp(self):
        os.environ['AWS_DEFAULT_REGION'] = \
            self.inputs.get('ec2_region_name')
        if self.password not in self.sensitive_data:
            self.sensitive_data.append(self.password)
        sys.stdout = PasswordFilter(self.sensitive_data, sys.stdout)
        sys.stderr = PasswordFilter(self.sensitive_data, sys.stderr)
        self.cfy_local = self.setup_cfy_local()
        if 'ECOSYSTEM_SESSION_MANAGER_IP' in os.environ:
            self.manager_ip = \
                os.environ['ECOSYSTEM_SESSION_MANAGER_IP']
        else:
            self.install_manager()
            self.initialize_manager_profile()

    @property
    def sensitive_data(self):
        return [
            os.environ['AWS_SECRET_ACCESS_KEY'],
            os.environ['AWS_ACCESS_KEY_ID']
        ]

    @property
    def node_type_prefix(self):
        return 'cloudify.nodes.aws'

    @property
    def plugin_mapping(self):
        return 'awssdk'

    @property
    def blueprint_file_name(self):
        return 'aws.yaml'

    @property
    def external_id_key(self):
        return 'aws_resource_id'

    @property
    def server_ip_property(self):
        return 'ip'

    @property
    def plugins_to_upload(self):
        """plugin yamls to upload to manager"""
        return [(DIAMOND_WAGON, DIAMOND_YAML),
                (HOST_POOL_WAGON, HOST_POOL_YAML)]

    @property
    def inputs(self):
        try:
            return {
                'password': os.environ['ECOSYSTEM_SESSION_PASSWORD'],
                'ec2_region_name': 'ap-southeast-1',
                'ec2_region_endpoint': 'ec2.ap-southeast-1.amazonaws.com',
                'availability_zone': 'ap-southeast-1b',
                'aws_access_key_id': os.environ['AWS_ACCESS_KEY_ID'],
                'aws_secret_access_key': os.environ['AWS_SECRET_ACCESS_KEY']
            }
        except KeyError:
            raise

    def check_resource_method(self):
        pass

    def test_blueprints_valid(self):
        for blueprint in ['aws', 'azure', 'gcp', 'openstack', 'hostpool']:
            failed = eco_utils.execute_command(
                'cfy blueprints upload {0}.yaml -b {0}-{1}'.format(
                    blueprint, self.application_prefix))
            if failed:
                raise Exception(
                    'Blueprint {0}-{1} must not be valid check logs.'.format(
                        blueprint, self.application_prefix))

    def test_kubernetes_blueprint(self):
        blueprint_path = 'tests/blueprint.yaml'
        blueprint_id = 'infra-{0}'.format(self.application_prefix)
        self.addCleanup(self.cleanup_deployment, blueprint_id)
        failed = eco_utils.execute_command(
            'cfy install {0} -b {1}'.format(blueprint_path, blueprint_id))
        if failed:
            raise NonRecoverableError(
                'Failed to install the infrastructure blueprint.')
        load_host = eco_utils.get_node_instances(
            'k8s_load_host', blueprint_id)[0]
        node_host = eco_utils.get_node_instances(
            'k8s_node_host', blueprint_id)[0]
        master_host = eco_utils.get_node_instances(
            'k8s_master_host', blueprint_id)[0]
        compute_blueprint_path = 'baremetal.yaml'
        compute_blueprint_id = 'kube-{0}'.format(self.application_prefix)
        self.addCleanup(self.cleanup_deployment, compute_blueprint_id)
        eco_utils.execute_command(
            'cfy blueprints upload {0} -b {1}'.format(
                compute_blueprint_path, compute_blueprint_id))
        eco_utils.create_deployment(compute_blueprint_id,
            {
                'public_master_ip': master_host.get(
                    'runtime_properties', {}).get('ip'),
                'k8s_node_host_ip': node_host.get(
                    'runtime_properties', {}).get('ip'),
                'k8s_load_host_ip': load_host.get(
                    'runtime_properties', {}).get('ip'),
                'agent_user': 'ec2-user',
                'dashboard_ip': master_host.get(
                    'runtime_properties', {}).get('public_ip_address')
            })
        eco_utils.execute_install(compute_blueprint_id)
        check_blueprint = eco_utils.install_nodecellar
        failed = check_blueprint(
            'examples/wordpress-blueprint.yaml',
            blueprint_archive=WORDPRESS,
            blueprint_id='wp')
        if failed:
            raise NonRecoverableError(
                'Failed to install the Wordpress blueprint.')
