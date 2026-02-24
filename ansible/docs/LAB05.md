# Lab 05 Report — Configuration Management with Ansible

## 1. Inventory & Configuration

* **Inventory**: A static `hosts.ini` file was used, containing the public IP address of the virtual machine created during Lab 04.

* **Variables**: All configuration settings, including ports, image names, and credentials, were externalized into `group_vars/all.yml` to maintain a clean separation between logic and data.

## 2. Secrets Management (Ansible Vault)

* **Ansible Vault** was implemented to secure the `dockerhub_password` and other sensitive data.

* The sensitive variable file was encrypted using the `ansible-vault encrypt` command.

* Playbooks are executed with the `--ask-vault-pass` flag to ensure secure decryption at runtime without storing the password in plain text.

## 3. Roles and Tasks

**Role**: `app_deploy`:

* **Docker Hub Authentication**: Logging into the registry to enable image pulling.

* **Image Management**: Pulling the latest version of the application image.

* **Container Lifecycle**: Stopping and removing existing containers to ensure a clean update, followed by launching a new container with updated parameters.

* **Healthcheck**: A `wait_for` task ensures the service is actually reachable on the designated port before marking the deployment as successful.

## 4. Execution Evidence

Screenshot of the `ansible-playbook` command output (showing the "recap" with successful tasks).

Screenshot of the browser or `curl` output displaying the JSON response from the application via the VM's public IP.

## 5. Best Practices Applied

* **Idempotency**: The playbook is designed to be idempotent. Subsequent runs will not perform any actions if the system state already matches the desired configuration (reporting `ok` instead of `changed`).

* **Separation of Concerns**: Deployment logic is `decoupled from environmental configuration through the use of Ansible Roles.

* **Security**: No passwords or sensitive tokens are stored in the git repository in plain text; all secrets are managed via encrypted Vault files.

* **Modularity**: The structure allows for easy scaling (e.g., adding more environments like `staging` or `production` by simply adding new inventory files).