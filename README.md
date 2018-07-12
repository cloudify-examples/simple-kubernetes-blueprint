[![Build Status](https://circleci.com/gh/cloudify-examples/simple-kubernetes-blueprint.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/cloudify-examples/simple-kubernetes-blueprint)

# Simple Kubernetes Blueprint

This blueprint installs a Kubernetes Cluster with the Cloudify Kubernetes Provider. See [documentation](http://docs.getcloudify.org/4.3.0/kubernetes/provider/#setup).


## Generic "bare metal" Example

You can deploy this blueprint on bare metal.

Requirements:

You need 3 separate machines, each with:

  * Network access and download ability.
  * Must be accessible via SSH
  * A `agent_key_private` secret containing the private key for the user Cloudify will authenticate with. Make sure that this private key value matches a public key in the authorized keys of each of the VMs.

The two kubernetes nodes accessible in `k8s_node_host_ip` and `public_master_ip` must have been setup with the script in `scripts/pre-install.sh`. Make sure to override `usermod -aG docker ec2-user` in that file.

**Installation:**

```bash
cfy install \
    https://github.com/cloudify-examples/simple-kubernetes-blueprint/archive/master.zip \
    -n compute.yaml -i agent_user=ec2-user \
    -i k8s_node_host_ip=10.10.4.84 \
    -i public_master_ip=10.10.4.177 \
    -i k8s_load_host_ip=10.10.4.87 \
    -i dashboard_ip=xxx.xxx.xxx.xxx \
    -b kubernetes
```

Some testing steps:

```shell
# Add the following environment variables:

export AWS_CENTOS_AMI=ami-b937f4d6
export AWS_INSTANCE_TYPE=t2.medium
export AWS_DEFAULT_REGION=eu-central-1
export AWS_SECRET_ACCESS_KEY=**********
export AWS_ACCESS_KEY_ID=**********
export AWS_TEST_KEY=agent_key_private
export AWS_SECURITY_GROUP=sg-001abc6c
export AWS_SUBNET_ID=subnet-dfa3dfa2

Install one Load Balancer VM:
aws ec2 run-instances \
    --image-id $AWS_CENTOS_AMI \
    --instance-type $AWS_INSTANCE_TYPE \
    --key-name $AWS_TEST_KEY \
    --subnet-id $AWS_SUBNET_ID \
    --associate-public-ip-address \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=lb}]'

# Install two Kubernetes VMs:
aws ec2 run-instances \
    --image-id $AWS_CENTOS_AMI \
    --instance-type $AWS_INSTANCE_TYPE \
    --key-name $AWS_TEST_KEY \
    --subnet-id $AWS_SUBNET_ID \
    --associate-public-ip-address \
    --user-data file://pre-install.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=k8s}]'
```
