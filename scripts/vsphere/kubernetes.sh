#!/bin/bash

cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg
	  https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOF

sudo setenforce 0

sudo yum -y install kubelet-1.9.3-0 kubeadm-1.9.3-0 kubectl-1.9.3-0 kubernetes-cni-0.6.0-0 ca-certificates
sudo update-ca-trust force-enable

sudo systemctl enable docker && systemctl start docker

# we need to disable swaps before use
swapon -s | awk '{print "sudo swapoff " $1}' | grep -v "Filename" | sh -

sudo sed -i 's|cgroup-driver=systemd|cgroup-driver=cgroupfs --provider-id='`hostname`'|g' /etc/systemd/system/kubelet.service.d/10-kubeadm.conf

ctx logger info "Reload kubernetes"

sudo systemctl daemon-reload
sudo systemctl enable kubelet.service
sudo systemctl stop kubelet && sleep 20 && sudo systemctl start kubelet

for retry_count in {1..10}
do
	status=`sudo systemctl status kubelet | grep "Active:"| awk '{print $2}'`
	ctx logger info "#${retry_count}: Kubelet state: ${status}"
	if [ "z$status" == 'zactive' ]; then
		break
	else
		ctx logger info "Wait little more."
		sleep 10
	fi
done
