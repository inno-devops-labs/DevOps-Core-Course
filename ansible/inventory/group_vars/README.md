# Group vars (vault) — used when you pass `-i inventory/hosts.ini`

When you run with **`-i inventory/hosts.ini`**, Ansible loads group_vars from **this** directory: `inventory/group_vars/all.yml`. It does **not** use `ansible/group_vars/all.yml`.

To add or change variables (e.g. image tag):

```bash
cd ansible
ansible-vault edit inventory/group_vars/all.yml
```

Add or set `docker_tag: lab03` or `docker_image_tag: lab03`. Save and run the playbook again.
