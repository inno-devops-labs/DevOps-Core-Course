# LAB04 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

**Provider:** Yandex Cloud – free tier, accessible in Russia.  
**VM:** standard-v2, 2 vCPU (20% fraction), 1 GB RAM, 10 GB HDD  
**Zone:** ru-central1-a  
**Network:** Custom VPC + subnet  
**Firewall:** SSH (22), HTTP (80), custom port 5000  
**Cost:** $0 (free tier)

**Resources Created:**
- VPC, Subnet  
- Security Group  
- Compute Instance (VM) with public IP

---

## 2. Terraform Implementation

**Terraform version:** 1.14.5 

**Structure:**
```
terraform/
├── main.tf          # VM, network, security group
├── variables.tf     # Input variables
├── outputs.tf       # Public IP
├── data.tf          # Ubuntu image
├── providers.tf     # Provider config
├── terraform.tfvars # Values (gitignored)
└── .gitignore
```

**Notes:**
- Variables for zone, instance type, SSH key  
- Security group only opens required ports  
- State local, sensitive files ignored  

**Commands & Output:**
- **Init & Plan**
`10-terraform-plan-output.png`
- **Apply**
`11-terraform-apply-output.png`


**SSH Test:**
```bash
ssh ubuntu@46.21.244.135

## Notes / Challenges

- For Yandex security groups, use `ipv4_cidr_blocks` instead of `cidr_blocks`.  
- Windows Defender initially blocked the Terraform provider binary; temporarily disabled to proceed. 
- `data.tf` used to fetch the latest Ubuntu 22.04 LTS image dynamically.  
- Terraform VM successfully created; Pulumi VM creation failed due to outdated `pulumi-yandex` SDK.  

---

## Pulumi Implementation

- Pulumi 3.x, Python  
- Project initialized, provider configured, but VM creation failed due to outdated `pulumi-yandex` SDK  
- Terraform VM retained for Lab 5  
- Pulumi code not applied  


**Comparison with Terraform:**  
- **Ease of Learning:** Terraform easier for beginners  
- **Code Readability:** Terraform clearer for small infrastructure  
- **Debugging:** Terraform CLI more straightforward  
- **Documentation:** Terraform more complete  
- **Use Case:** Terraform for repeatable infrastructure; Pulumi for dynamic/programmatic infrastructure  

---

## Lab 5 Preparation & Cleanup

- **VM for Lab 5:** Terraform-created VM retained  
- **Pulumi Resources:** Not applied  
- **SSH Access Verified for Terraform VM**  

**Key Takeaways:**  
- Terraform is stable and reliable with Yandex Cloud  
- Pulumi requires up-to-date provider SDKs  
- Always check provider arguments in documentation  
- `.gitignore` critical for credentials and state files  
- Keeping one VM between labs saves time and avoids re-provisioning  

---

**Summary:** Lab 4 completed with Terraform; Pulumi attempt unsuccessful. VM preserved for Lab 5 work.  