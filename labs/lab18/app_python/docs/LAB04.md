# Documentation

## Cloud provider and infrastructure

### Cloud provider chosen and rationale

- I chose Yandex Cloud since it provides solid resource provision with a lot of RAM and storage space, also it has a free trial period.

### Instance type/size and why

- 2 cpu cores and 2 gb of ram because the project is really small and we don't need a lot of resources for it.

### Region/zone selected

- zone ru-central1-a

### Resources created (list all)

- service account

- boot disk with ubuntu image

- vm (2 cores, 2 memory)

- network

- subnet (zone ru-central1-a)

- security group

## Task 1 (Terraform implementation)

### Terraform version used

Terraform v1.14.5 on darwin_arm64

### Project structure explanation

```
app_python/
├── pulumi/
│   ├── venv/                # Python virtual environment
│   ├── Pulumi.yaml          # Pulumi project metadata
│   ├── Pulumi.dev.yaml      # Stack config (gitignored)
│   ├── requirements.txt     # Python dependencies
│   ├── __main__.py          # Pulumi infrastructure code
|   ├── .gitignore           # Ignore state, credentials
│   └── README.md            # Pulumi setup instructions
└── terraform/
    ├── .gitignore           # Ignore state, credentials
    ├── main.tf              # Main resources
    ├── variables.tf         # Input variables
    ├── outputs.tf           # Output values
    ├── terraform.tfvars     # Variable values (gitignored)
    └── README.md            # Terraform setup instructions
```

### Key configuration decisions

- connect with pair of SSH keys
- configure security group rules
- expose only necessary ports
- do not expose credentials

### Challenges encountered

Getting accustomed to the Yandex Cloud wasn't easy, and setting up SSH connection also was a little challanging.

### Public IP address of created VM

```bash
external_ip_address_vm = "62.84.117.91"
```

### SSH connection command

```bash
ssh -i /home-directory/.ssh/terraform-vm-key ubuntu@62.84.117.91
```

### Terminal output from terraform plan and terraform apply

![Plan](./screenshots/lab04-shots/terraform%20plan.png)

![Apply-1](./screenshots/lab04-shots/terraform%20apply-1.png)

![Apply-2](./screenshots/lab04-shots/terraform%20apply-2.png)

### Proof of SSH access to VM

![SSH](./screenshots/lab04-shots/ssh%20output%20terraform.png)

## Task 2 (Pulumi Implementation)

### Pulumi version and language used

- pulumi==3.222.0, python

### Terraform destroy output

![](./screenshots/lab04-shots/terraform%20destroy.png)

### How code differs from Terraform

- Palumi supports many programming language for configuration, while terraform only lets to use its default config language.

### Advantages you discovered

- It is easier to write in a familiar language in Palumi, but to be honest, I enjoyed writing terraform config more.

### Challenges encountered

- Had problems with SSH as well, also it wasn't so easy to find documentation and guides.

### Terminal output

- pulumi preview

![](./screenshots/lab04-shots/pulumi%20preview.png)

- pulumi up
![](./screenshots/lab04-shots/pulumi%20up.png)

- SSH connection to VM

![](./screenshots/lab04-shots/pulumi%20ssh.png)

### Public IP of Pulumi-created VM

```bash
(venv) fountainer@Veronicas-MacBook-Air pulumi % pulumi stack output

Enter your passphrase to unlock config/secrets
    (set PULUMI_CONFIG_PASSPHRASE or PULUMI_CONFIG_PASSPHRASE_FILE to remember):  
Enter your passphrase to unlock config/secrets
Current stack outputs (2):
    OUTPUT       VALUE
    external_ip  93.77.185.195
    internal_ip  192.168.10.5
```
### SSH connection

(I reused the key from the terraform config)

```bash
ssh -i ~/.ssh/terraform-vm-key ubuntu@93.77.185.195
```

![](./screenshots/lab04-shots/pulumi%20ssh.png)

## Terraform vs Pulumi Comparison

### Ease of Learning: Which was easier to learn and why?

- Documentation for Terraform was easier to find (for me), but Polumi was more familiar to work with. I also felt like Polumni's config is less complex.

### Code Readability: Which is more readable for you?

- Terraform

### Debugging: Which was easier to debug when things went wrong?

- Terraform, plan command was really useful

### Documentation: Which has better docs and examples?

- Terraform

### Use Case: When would you use Terraform? When Pulumi?

- Pulumi is good for projects where you want to employ features that only conplex programming languages can provide. Terraform is good for standardized infrastructure.

### Code differences (HCL vs Python/TypeScript)

- Terraform uses declarative HCL with blocks and attributes, while Pulumi uses imperative Python/TypeScript with function calls, objects, and full programming language features for resource creation and logic.

### Which tool you prefer and why

- I liked Terraform more (partially because on this step I was creating a vm in the cloud for the first time, but doing the same with Palumi was quite boring), I like the declarative languages, and they seem to be intuitively understandable.

## Lab 5 Preparation & Cleanup

### Are you keeping your VM for Lab 5? (Yes/No)

- Yes

### If yes: Which VM (Terraform or Pulumi created)?

- Palumi, but I kind of contemplating on returning to Terraform...

### VM Status

![](./screenshots/lab04-shots/vm%20status.png)





