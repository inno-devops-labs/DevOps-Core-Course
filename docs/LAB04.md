# Lab 4 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure
- **Cloud Provider:** AWS (Amazon Web Services)
- **Rationale:** I chose AWS because I have a student account with free credits, making it a cost-effective option for this lab.
- **Instance Type/Size:** `t2.micro`, as it is eligible for the AWS Free Tier.
- **Region/Zone:** `us-east-1`
- **Total Cost:** $0 (using the Free Tier)
- **Resources Created:**
    - `aws_vpc`
    - `aws_subnet`
    - `aws_internet_gateway`
    - `aws_route_table`
    - `aws_route_table_association`
    - `aws_security_group`
    - `aws_key_pair`
    - `aws_instance`

## 2. Terraform Implementation
- **Terraform Version:** 1.14.5
- **Project Structure:**
    - `main.tf`: Contains the main infrastructure resources.
    - `variables.tf`: Defines input variables for the configuration.
    - `outputs.tf`: Specifies the output values, such as the public IP address.
    - `.gitignore`: Excludes sensitive files from version control.
- **Key Configuration Decisions:**
    - Used a data source to dynamically find the latest Ubuntu 20.04 AMI.
    - Created a new VPC and subnet to ensure a clean and isolated environment.
    - Configured a security group to allow SSH (port 22), HTTP (port 80), and custom port 5000.
- **Challenges Encountered:**
    - Initially, Terraform was not in the system's PATH, so I had to use the full path to the executable.
- **Terminal Output:**
    - **`terraform plan`:**
    ```
    ... (plan output) ...
    ```
    - **`terraform apply`:**
    ```
    ... (apply output) ...
    ```
    - **SSH Connection:**
    ```
    ssh -i ~/.ssh/id_rsa ubuntu@44.193.82.57
    ```

## 3. Pulumi Implementation
- **Pulumi Version:** 3.222.0
- **Language:** Python
- **How Code Differs from Terraform:**
    - Pulumi uses a general-purpose programming language (Python) instead of a domain-specific language (HCL).
    - The code is more imperative, defining resources as objects and using standard Python libraries.
- **Advantages Discovered:**
    - The ability to use familiar programming constructs like loops and conditionals.
    - Better integration with IDEs, providing features like autocompletion and type checking.
- **Challenges Encountered:**
    - Similar to Terraform, Pulumi was not in the system's PATH.
    - I encountered an `AttributeError` because I was using `aws.get_ami` instead of `aws.ec2.get_ami`.
- **Terminal Output:**
    - **`pulumi preview`:**
    ```
    ... (preview output) ...
    ```
    - **`pulumi up`:**
    ```
    ... (up output) ...
    ```
    - **SSH Connection:**
    ```
    ssh -i ~/.ssh/id_rsa ubuntu@3.95.64.201
    ```

## 4. Terraform vs Pulumi Comparison
- **Ease of Learning:** For me, Terraform was slightly easier to learn due to its simpler, declarative syntax.
- **Code Readability:** I find Pulumi's Python code more readable because I am already familiar with the language.
- **Debugging:** Debugging in Pulumi felt more natural, as I could use standard Python debugging tools and techniques.
- **Documentation:** Both tools have excellent documentation, but I found Pulumi's examples to be more helpful.
- **Use Case:** I would use Terraform for smaller, more straightforward projects, and Pulumi for more complex infrastructure with dynamic components.

## 5. Lab 5 Preparation & Cleanup
- **VM for Lab 5:** Yes, I will keep the Pulumi-created VM for Lab 5.
- **Cleanup Status:** The Terraform-created resources have been destroyed.
