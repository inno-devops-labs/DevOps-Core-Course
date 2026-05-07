# LAB 04

## Local VM Alternative

### Task 1, show VM creation
I use VirtualBox. I added screenshots with my configuration in `images` folder.

### Steps:
1. I created new VM manualy (OS: Ubunty 22.04)
2. I installed `openssh-server` there
3. I created ssh key-pair on my host machine (Windows 10)
4. I added public ssh key into VM
5. I configures VM to use Bridge connection (this will give my VM its own ip in my home net)
6. I established connection to VM from my host machine


### Note
I really tried to configure terraform for 2 days. You may say "skill-issue", but yes, nothing is working. Half of things need VPN to run, half of them don't run with VPN.
I tried - I failed. I accept it, as I have another option provided in the lab.
Even if I failed, I learned new things about terraform. Yeah, not how to run it by myself of cousre, but still.