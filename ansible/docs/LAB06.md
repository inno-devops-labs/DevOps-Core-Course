# Lab 6: Advanced Ansible & CI/CD

**Name:** Daniil Mayorov
**Date:** 2005-08-21

## Overview

In this lab the infrastructure automation from the previous lab was extended using advanced features of Ansible.

The following improvements were implemented:

* task grouping with blocks
* selective execution with tags
* application deployment using Docker Compose
* role dependencies
* wipe logic for safe application removal
* automated deployment using GitHub Actions

The application is deployed as a container from Docker Hub and managed through Ansible roles.

---

# Task 1: Blocks & Tags

Blocks were used to group related tasks and apply common directives such as `become`, `when`, and `tags`.

Example pattern used in roles:

![Example pattern used in roles](/ansible/docs/screenshots/lab6/example_pattern_used_in_roles.png)

Tags allow selective execution of tasks.

Example:

![empl tags execution](/ansible/docs/screenshots/lab6/tag_docker.png)


Tags used in the project:

| Tag            | Purpose                   |
| -------------- | ------------------------- |
| common | entire common role |
| packages | package installation |
| users | user creation |
| docker | docker role |
| docker_install | docker installation |
| docker_config | docker configuration |
| app_wipe | web app wipe |

---

# Task 2: Docker Compose Deployment

The application deployment was migrated from manual container execution to Docker Compose.

Advantages:

* declarative configuration
* easier updates
* reproducible deployments
* simpler multi-container support

The compose configuration is generated using a Jinja2 template.

Example template:

![Jinja2 template](/ansible/docs/screenshots/lab6/jinja2template.png)

Variables used:

* `app_name`
* `docker_image`
* `docker_tag`
* `app_port`
* `app_internal_port`
* `compose_project_dir`

---

# Task 3: Wipe Logic

Wipe logic was implemented to safely remove deployed applications.

The wipe mechanism uses **double protection**:

1. variable `app_wipe`
2. tag `app_wipe`

Default configuration:

```yaml
app_wipe: false
```

Wipe tasks perform:

* stopping containers
* removing docker-compose configuration
* removing application directory

Example wipe command:

![app wipe](/ansible/docs/screenshots/lab6/app_wipe.png)

Example clean reinstall:

![wipe2](/ansible/docs/screenshots/lab6/wipe2.png)

Execution order:

```
wipe tasks → deployment tasks
```

This allows clean reinstallation of the application.

---

# Testing Results

The deployment process was tested with the following scenarios:

**Normal deployment**

![normal dep](/ansible/docs/screenshots/lab6/playbook-1.png)


**Idempotency test**

![idem1](/ansible/docs/screenshots/lab6/playbook-2.png)
![idem2](/ansible/docs/screenshots/lab6/playbook-2.png)
![idem3](/ansible/docs/screenshots/lab6/playbook-3.png)
![idem4](/ansible/docs/screenshots/lab6/playbook-4.png)

**Selective execution**

![sel-doc](/ansible/docs/screenshots/lab6/tag_docker.png)

Only Docker tasks were executed.

---

# Challenges & Solutions

**Docker module errors**

The Docker modules required additional Python dependencies on the target host.
This was solved by installing `python3-docker`.

**Template variable errors**

Incorrect variable names in the compose template caused deployment failures.
This was fixed by aligning variable names with `group_vars`.

**CI/CD authentication**

SSH authentication required storing private keys in GitHub Secrets.

---

# Research Answers

### What happens if rescue block also fails?

If the rescue block fails, the task is marked as failed and Ansible stops execution of the play unless errors are ignored.

---

### Can you have nested blocks?

Yes. Ansible allows nested blocks, but it is recommended to keep them shallow to maintain readability.

---

### How do tags inherit inside blocks?

Tags defined on a block automatically apply to all tasks inside the block.

---

### Difference between `restart: always` and `restart: unless-stopped`?

* `always` - container always restarts, even after manual stop
* `unless-stopped` - container restarts automatically unless it was manually stopped

---

### Why use both variable and tag for wipe logic?

This provides a **double safety mechanism**:

* tag ensures wipe tasks are not executed during normal runs
* variable ensures wipe does not run accidentally if the tag is used

Both conditions must be satisfied.

---

### Difference between `never` tag and this approach?

`never` prevents tasks from running unless explicitly called.
The variable + tag approach provides more flexible control and safer execution.

---

### Why must wipe logic run before deployment?

It allows **clean reinstallation**:

```
wipe old installation → deploy new version
```

Without this order the old containers might conflict with new deployment.

---

### Security implications of storing SSH keys in GitHub Secrets?

Secrets are encrypted and not visible in logs, but if a repository is compromised the attacker may gain access to the stored credentials.

---

### How to implement staging -> production deployment?

Two environments can be created with separate inventories:

```
inventory/staging
inventory/production
```

CI/CD first deploys to staging, runs tests, then deploys to production.

---

### How would you add rollback support?

Rollback can be implemented by:

* storing previous Docker image tags
* redeploying a previous version
* keeping versioned releases in Docker Hub.