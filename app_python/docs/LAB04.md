# Lab 4 - Infrastructure as Code

I used a local VM instead of using a cloud provider.

Instead of VirtualBox or VMWare I chose QEMU KVM with libvirt, because I am most familiar with it.

## VM Setup

First install all packages on the host system.

```bash
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst
```

After installing, create a system image for the guest system

```bash
sudo qemu-img create -f qcow2 /var/lib/libvirt/images/devops-lab4-vm.qcow2 10G
```

Output

```
Formatting '/var/lib/libvirt/images/devops-lab4-vm.qcow2', fmt=qcow2 cluster_size=65536 extended_l2=off compression_type=zlib size=10737418240 lazy_refcounts=off refcount_bits=16
```

Check the name of the bridge interface on the host system

```bash
ip a
```

Output

```
...
7: virbr0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default qlen 1000
    link/ether 52:54:00:f2:98:90 brd ff:ff:ff:ff:ff:ff
    inet 192.168.122.1/24 brd 192.168.122.255 scope global virbr0
       valid_lft forever preferred_lft forever
```

Install vm

```bash
sudo virt-install --name devops-lab4-vm --memory 2048 --vcpus 1 --disk path=/var/lib/libvirt/images/devops-lab4-vm.qcow2,bus=virtio --network bridge=virbr0,model=virtio --os-variant ubuntu24.04 --location /var/lib/libvirt/images/ubuntu-24.04.4-live-server-amd64.iso,kernel=casper/vmlinuz,initrd=casper/initrd --graphics none --console pty,target_type=serial --extra-args 'console=ttyS0,115200n8 serial'
```

Parameters explanation:

- `--name` created vm name
- `--memory` created vm ram size
- `--vcups` number of virtual cpu cores vm has access to
- `--disk` vm disk configuration
  - `path=...` path to the disk image
  - `bus=virtio` virtual device type used by the vm to communicate with the host
- `--network` network configuration
  - `bridge=virbr0` name of the vm bridge network interface on the host we got in the previous step
  - `model=virtio` virtual device type used by the vm to communicate with the host
- `--os-variant` guest os type for improved guest system compatibility
- `--cdrom` cdrom device. In this case it is the ubuntu server 24.04 install image.
- `--graphics` graphics devices. In this case it is none since we will communicate with the guest tty using serial, and then using ssh.
- `--console` set parameters for viewing the console
- `--extra-args` extra arguments in order to view the guest system tty in serial.

After waiting for the guest to turn on, we see the following window

```
================================================================================
  Serial                                                              [ Help ]
================================================================================

  As the installer is running on a serial console, it has started in basic
  mode, using only the ASCII character set and black and white colours.

  If you are connecting from a terminal emulator such as gnome-terminal that
  supports unicode and rich colours you can switch to "rich mode" which uses
  unicode, colours and supports many languages.

  You can also connect to the installer over the network via SSH, which will
  allow use of rich mode.







                          [ Continue in rich mode  > ]
                          [ Continue in basic mode > ]
                          [ View SSH instructions    ]

```

Install the guest vm by selecting the defaults. After some steps, on the SSH configuration screen enable Install OpenSSH server. Do not press Import SSH key as it requires to use GitHub or launchpad. The "Allow password authentication over SSH" option can not be toggled off. The keys will be imported after install.

```
================================================================================
  SSH configuration                                                   [ Help ]
================================================================================
  You can choose to install the OpenSSH server package to enable secure remote
  access to your server.

  [X]  Install OpenSSH server


  [X]  Allow password authentication over SSH


  [ Import SSH key > ]

  AUTHORIZED KEYS

    No authorized key




                                 [ Done       ]
                                 [ Back       ]

```

Reboot after the installation is complete. Add the public ssh key generated on the host to the authorized keys.

```
cirno@devops-lab4-vm:~$ echo 'public key' > ~/.ssh/authorized_keys
cirno@devops-lab4-vm:~$ chmod 700 ~/.ssh/
cirno@devops-lab4-vm:~$ chmod 600 ~/.ssh/authorized_keys
cirno@devops-lab4-vm:~$
```

Since you are not allowed to disable password authentication on the install screen. We now need to edit the sshd configuration file. The installed ubuntu server does not come with any visual editors, so we need to install vim and edit the sshd configuration file.

```
cirno@devops-lab4-vm:~$ sudo apt install vim
cirno@devops-lab4-vm:~$ vim /etc/ssh/sshd_config
```

Uncomment the PasswordAuthentication line and change it to no to disable password authentication.

```

# For this to work you will also need host keys in /etc/ssh/ssh_known_hosts
#HostbasedAuthentication no
# Change to yes if you don't trust ~/.ssh/known_hosts for
# HostbasedAuthentication
#IgnoreUserKnownHosts no
# Don't read the user's ~/.rhosts and ~/.shosts files
#IgnoreRhosts yes

# To disable tunneled clear text passwords, change to no here!
PasswordAuthentication no
#PermitEmptyPasswords no

# Change to yes to enable challenge-response passwords (beware issues with
# some PAM modules and threads)
KbdInteractiveAuthentication no

# Kerberos options
#KerberosAuthentication no
#KerberosOrLocalPasswd yes
#KerberosTicketCleanup yes
#KerberosGetAFSToken no

                                                              68,0-1        50%
```

Save the configuration file and restart the sshd service to reload the configuration.

```
cirno@devops-lab4-vm:~$ sudo systemctl restart ssh.service
cirno@devops-lab4-vm:~$ 
```

View the ip address of the vm.

```
cirno@devops-lab4-vm:~$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host noprefixroute 
       valid_lft forever preferred_lft forever
2: enp1s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 52:54:00:c3:80:49 brd ff:ff:ff:ff:ff:ff
    inet 192.168.122.243/24 metric 100 brd 192.168.122.255 scope global dynamic enp1s0
       valid_lft 3169sec preferred_lft 3169sec
    inet6 fe80::5054:ff:fec3:8049/64 scope link 
       valid_lft forever preferred_lft forever
cirno@devops-lab4-vm:~$ 
```

SSH into the vm from the host system.

```
cirno@t14-devops:~/Documents/DevOps-Core-Course$ ssh cirno@192.168.122.243
The authenticity of host '192.168.122.243 (192.168.122.243)' can't be established.
ED25519 key fingerprint is SHA256:fingerprint.
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '192.168.122.243' (ED25519) to the list of known hosts.
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

This system has been minimized by removing packages and content that are
not required on a system that users do not log into.

To restore this content, you can run the 'unminimize' command.
cirno@devops-lab4-vm:~$ free -h
               total        used        free      shared  buff/cache   available
Mem:           1.9Gi       292Mi       1.4Gi       800Ki       400Mi       1.6Gi
Swap:          1.5Gi          0B       1.5Gi
cirno@devops-lab4-vm:~$ cat /etc/os-release 
PRETTY_NAME="Ubuntu 24.04.4 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.4 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=noble
LOGO=ubuntu-logo
cirno@devops-lab4-vm:~$ 
```

Everything works. The guest system has ssh server configured with authorization only through ssh keys. The host system is able to ssh into the guest system using the ssh key.
