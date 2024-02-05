# Automated build of k3s cluster with optional HA control plane

This playbook will build an HA Kubernetes cluster using `k3s`.

Optional HA support is based on `kube-vip` and MetalLB. It uses [kube-vip](https://kube-vip.io/)
to create a load balancer for control plane, and [metal-lb](https://metallb.universe.tf/installation/)
for its service `LoadBalancer`.


## Node requirements

To install k3s as a distribution package:

- [x] Arch Linux

To directly install k3s binary:

- [x] Any systemd-based distribution, or specifically:
  - [x] Debian (tested on version 11)
  - [x] Ubuntu (tested on version 22.04)
  - [x] Rocky (tested on version 9)

- [x] Any of these CPU architectures:
  - [X] x64
  - [X] aarch64
  - [X] armv7l


## Controller requirements

This playbook uses custom plugins and advanced Ansible functionality.
The following requirements were used during the development:

- [x] Ansible 2.16.3
  - [x] `community.general` collection is required
- [x] Python 3.11
- [x] jq
- [x] python-netaddr


## Usage

### Preparation

1. Make a copy of `inventory/sample`:

    ```bash
    cp -R inventory/sample inventory/my
    ```

2. Edit `inventory/my/hosts.yaml`
    - Specify master nodes under `k3s_server` (these nodes will run k3s control plane)
    - Specify worker nodes under `k3s_agent` (these nodes will only run the workload)

    ```yaml
    k3s:
      children:
        k3s_server:
          hosts:
            node1.mydomain:
        k3s_agent:
          hosta:
            node2.mydomain:
            node3.mydomain:
    ````

    If multiple hosts are in the `k3s_server` group, the playbook will automatically
    set up k3s in [HA mode with etcd](https://rancher.com/docs/k3s/latest/en/installation/ha-embedded/).

3. If needed, edit `inventory/my/group_vars/all.yml` to adjust deployment settings
to match your environment.

4. Finally, edit `ansible.cfg` and update the inventory path to `inventory/my`
or the directory you have just created.

### Provisioning

Create the cluster using the follosing command:

```bash
ansible-playbook site.yml --tags never
```

> [!IMPORTANT]
> Roles that have the potential to break an existing deployment or cause
> a service interruption are marked with `tags: never`.

After deployment, the control plane will be accessible via the VIP (virtual IP
address) specified as `vip.apiserver_ip` in the group_vars.

### Deprovisioning

Destroy the cluster using the following command:

```bash
ansible-playbook reset.yml
```

> [!IMPORTANT]  
> You should also reboot the nodes, particularly if HA was used.

### `kubeconfig`

After provisioning, the kubeconfig with adjusted apiserver endpoint and
context name will be available in the `_out` directory on the control node.


## Meta

> [!CAUTION]
> This information is potentially obsolete as it was inherited from the playbook
> this work was based on.

### Testing the playbook using molecule

This playbook includes a [molecule](https://molecule.rtfd.io/)-based test setup.
It is run automatically in CI, but you can also run the tests locally.
This might be helpful for quick feedback in a few cases.
You can find more information about it [here](molecule/README.md).

### Pre-commit Hooks

This repo uses `pre-commit` and `pre-commit-hooks` to lint and fix common style and syntax errors.
Be sure to install python packages and then run `pre-commit install`.
For more information, see [pre-commit](https://pre-commit.com/)


## Previous work

- [techno-tim/k3s-ansible](https://github.com/techno-tim/k3s-ansible.git)
- [k3s-io/k3s-ansible](https://github.com/k3s-io/k3s-ansible)
- [geerlingguy/turing-pi-cluster](https://github.com/geerlingguy/turing-pi-cluster)
- [212850a/k3s-ansible](https://github.com/212850a/k3s-ansible)
