# Using an existing Ansible Role for Docker

## Testing playbook

```bash
ansible-playbook -i inventory/local.yaml playbooks/dev/geerlingguy.yaml


PLAY [Install predefined docker role] ********************************************************************

TASK [Gathering Facts] ***********************************************************************************
ok: [test_host]

TASK [geerlingguy.docker : Load OS-specific vars.] *******************************************************
ok: [test_host]

TASK [geerlingguy.docker : include_tasks] ****************************************************************
skipping: [test_host]

TASK [geerlingguy.docker : include_tasks] ****************************************************************
skipping: [test_host]

TASK [geerlingguy.docker : Install Docker packages.] *****************************************************
ok: [test_host]

TASK [geerlingguy.docker : Install Docker packages (with downgrade option).] *****************************
skipping: [test_host]

TASK [geerlingguy.docker : Install docker-compose plugin.] ***********************************************
ok: [test_host]

TASK [geerlingguy.docker : Install docker-compose-plugin (with downgrade option).] ***********************
skipping: [test_host]

TASK [geerlingguy.docker : Ensure /etc/docker/ directory exists.] ****************************************
skipping: [test_host]

TASK [geerlingguy.docker : Configure Docker daemon options.] *********************************************
skipping: [test_host]

TASK [geerlingguy.docker : Ensure Docker is started and enabled at boot.] ********************************
ok: [test_host]

TASK [geerlingguy.docker : Ensure handlers are notified now to avoid firewall conflicts.] ****************

TASK [geerlingguy.docker : include_tasks] ****************************************************************
skipping: [test_host]

TASK [geerlingguy.docker : Get docker group info using getent.] ******************************************
skipping: [test_host]

TASK [geerlingguy.docker : Check if there are any users to add to the docker group.] *********************
skipping: [test_host]

TASK [geerlingguy.docker : include_tasks] ****************************************************************
skipping: [test_host]

PLAY [Verify Docker Installation] ************************************************************************

TASK [Gathering Facts] ***********************************************************************************
ok: [test_host]

TASK [Check Docker Version] ******************************************************************************
ok: [test_host]

TASK [Display Docker Version] ****************************************************************************
ok: [test_host] => {
    "msg": "Installed Docker version: Docker version 27.3.1, build ce1223035a"
}

PLAY RECAP ***********************************************************************************************
test_host                  : ok=8    changed=0    unreachable=0    failed=0    skipped=10   rescued=0    ignored=0
```

## Custom Docker Role

### --check

```bash
 ansible-playbook -i inventory/local.yaml playbooks/dev/main.yaml --syntax-check

playbook: playbooks/dev/main.yaml
```

### execute playbook on local

```bash
 ansible-playbook -i inventory/local.yaml playbooks/dev/main.yaml


PLAY [all] ***********************************************************************************************

TASK [Gathering Facts] ***********************************************************************************
ok: [test_host]

TASK [docker : Install docker] ***************************************************************************
included: /home/sofia/innop/spr2025/dev-ops/S25-core-course-labs/ansible/roles/docker/tasks/install_docker.yml for test_host

TASK [docker : Update apt package index] *****************************************************************
ok: [test_host]

TASK [docker : Install required system packages] *********************************************************
ok: [test_host] => (item=apt-transport-https)
ok: [test_host] => (item=ca-certificates)
ok: [test_host] => (item=curl)
ok: [test_host] => (item=gnupg-agent)
ok: [test_host] => (item=software-properties-common)

TASK [docker : Add Docker's official GPG key] ************************************************************
ok: [test_host]

TASK [docker : Add Docker's official apt repository] *****************************************************
ok: [test_host]

TASK [docker : Install Docker and dependencies] **********************************************************
ok: [test_host] => (item=docker-ce)
ok: [test_host] => (item=docker-ce-cli)
ok: [test_host] => (item=containerd.io)

TASK [docker : Install docker-compose] *******************************************************************
included: /home/sofia/innop/spr2025/dev-ops/S25-core-course-labs/ansible/roles/docker/tasks/install_docker-compose.yml for test_host

TASK [docker : Download Docker Compose] ******************************************************************
ok: [test_host]

TASK [docker : Initialize docker service] ****************************************************************
included: /home/sofia/innop/spr2025/dev-ops/S25-core-course-labs/ansible/roles/docker/tasks/init_docker-service.yml for test_host

TASK [docker : Add user to docker group] *****************************************************************
changed: [test_host]

TASK [docker : Configure Docker daemon security] *********************************************************
changed: [test_host]

TASK [docker : Detect init system] ***********************************************************************
ok: [test_host]

TASK [docker : Enable Docker service (Systemd only)] *****************************************************
skipping: [test_host]

TASK [docker : Restart Docker (Systemd only)] ************************************************************
skipping: [test_host]

TASK [docker : Restart Docker (Service)] *****************************************************************
changed: [test_host]

RUNNING HANDLER [docker : Restart Docker] ****************************************************************
changed: [test_host]

PLAY [Verify Docker Installation] ************************************************************************

TASK [Gathering Facts] ***********************************************************************************
ok: [test_host]

TASK [Check Docker Version] ******************************************************************************
ok: [test_host]

TASK [Display Docker Version] ****************************************************************************
ok: [test_host] => {
    "msg": "Installed Docker version: Docker version 27.5.1, build 9f9e405"
}

PLAY RECAP ***********************************************************************************************
test_host                  : ok=18   changed=4    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0

```

### ansible inventory --list

```
{
    "_meta": {
        "hostvars": {
            "test_host": {
                "ansible_all_ipv4_addresses": [
                    {
                        "__ansible_unsafe": "172.17.0.1"
                    },
                    {
                        "__ansible_unsafe": "172.18.0.1"
                    },
                    {
                        "__ansible_unsafe": "10.91.51.42"
                    },
                    {
                        "__ansible_unsafe": "10.244.53.78"
                    },
                    {
                        "__ansible_unsafe": "192.168.1.160"
                    }
                ],
                "ansible_all_ipv6_addresses": [
                    {
                        "__ansible_unsafe": "fe80::42:33ff:fe82:5e88"
                    },
                    {
                        "__ansible_unsafe": "fe80::9eaa:991c:ae5a:7c1e"
                    },
                    {
                        "__ansible_unsafe": "fe80::5c2a:7aff:fe90:53ad"
                    },
                    {
                        "__ansible_unsafe": "fe80::f09a:67ff:fec1:efad"
                    }
                ],
                "ansible_apparmor": {
                    "status": {
                        "__ansible_unsafe": "disabled"
                    }
                },
                "ansible_architecture": {
                    "__ansible_unsafe": "x86_64"
                },
                "ansible_bios_date": {
                    "__ansible_unsafe": "02/03/2021"
                },
                "ansible_bios_vendor": {
                    "__ansible_unsafe": "LENOVO"
                },
                "ansible_bios_version": {
                    "__ansible_unsafe": "G5CN16WW(V1.04)"
                },
                "ansible_board_asset_tag": {
                    "__ansible_unsafe": "NO Asset Tag"
                },
                "ansible_board_name": {
                    "__ansible_unsafe": "LNVNB161216"
                },
                "ansible_board_serial": {
                    "__ansible_unsafe": "MP1ZS5RF"
                },
                "ansible_board_vendor": {
                    "__ansible_unsafe": "LENOVO"
                },
                "ansible_board_version": {
                    "__ansible_unsafe": "No DPK"
                },
                "ansible_br_8cfa35c2750f": {
                    "active": false,
                    "device": {
                        "__ansible_unsafe": "br-8cfa35c2750f"
                    },
                    "id": {
                        "__ansible_unsafe": "8000.0242d47029f4"
                    },
                    "interfaces": [],
                    "ipv4": {
                        "address": {
                            "__ansible_unsafe": "172.18.0.1"
                        },
                        "broadcast": {
                            "__ansible_unsafe": "172.18.255.255"
                        },
                        "netmask": {
                            "__ansible_unsafe": "255.255.0.0"
                        },
                        "network": {
                            "__ansible_unsafe": "172.18.0.0"
                        },
                        "prefix": {
                            "__ansible_unsafe": "16"
                        }
                    },
                    "macaddress": {
                        "__ansible_unsafe": "02:42:d4:70:29:f4"
                    },
                    "mtu": 1500,
                    "promisc": false,
                    "speed": -1,
                    "stp": false,
                    "type": {
                        "__ansible_unsafe": "bridge"
                    }
                },
                "ansible_chassis_asset_tag": {
                    "__ansible_unsafe": "NO Asset Tag"
                },
                "ansible_chassis_serial": {
                    "__ansible_unsafe": "MP1ZS5RF"
                },
                "ansible_chassis_vendor": {
                    "__ansible_unsafe": "LENOVO"
                },
                "ansible_chassis_version": {
                    "__ansible_unsafe": "IdeaPad 5 14ALC05"
                },
                "ansible_cmdline": {
                    "BOOT_IMAGE": {
                        "__ansible_unsafe": "/vmlinuz-linux"
                    },
                    "loglevel": {
                        "__ansible_unsafe": "3"
                    },
                    "quiet": true,
                    "root": {
                        "__ansible_unsafe": "UUID=cf7c794f-dad7-4c4b-a880-3fe6c388b903"
                    },
                    "rw": true
                },
                "ansible_connection": "ssh",
                "ansible_date_time": {
                    "date": {
                        "__ansible_unsafe": "2025-02-09"
                    },
                    "day": {
                        "__ansible_unsafe": "09"
                    },
                    "epoch": {
                        "__ansible_unsafe": "1739094581"
                    },
                    "epoch_int": {
                        "__ansible_unsafe": "1739094581"
                    },
                    "hour": {
                        "__ansible_unsafe": "09"
                    },
                    "iso8601": {
                        "__ansible_unsafe": "2025-02-09T09:49:41Z"
                    },
                    "iso8601_basic": {
                        "__ansible_unsafe": "20250209T094941487907"
                    },
                    "iso8601_basic_short": {
                        "__ansible_unsafe": "20250209T094941"
                    },
                    "iso8601_micro": {
                        "__ansible_unsafe": "2025-02-09T09:49:41.487907Z"
                    },
                    "minute": {
                        "__ansible_unsafe": "49"
                    },
                    "month": {
                        "__ansible_unsafe": "02"
                    },
                    "second": {
                        "__ansible_unsafe": "41"
                    },
                    "time": {
                        "__ansible_unsafe": "09:49:41"
                    },
                    "tz": {
                        "__ansible_unsafe": "UTC"
                    },
                    "tz_dst": {
                        "__ansible_unsafe": "UTC"
                    },
                    "tz_offset": {
                        "__ansible_unsafe": "+0000"
                    },
                    "weekday": {
                        "__ansible_unsafe": "Sunday"
                    },
                    "weekday_number": {
                        "__ansible_unsafe": "0"
                    },
                    "weeknumber": {
                        "__ansible_unsafe": "05"
                    },
                    "year": {
                        "__ansible_unsafe": "2025"
                    }
                },
                "ansible_default_ipv4": {
                    "address": {
                        "__ansible_unsafe": "192.168.1.160"
                    },
                    "alias": {
                        "__ansible_unsafe": "vpn0"
                    },
                    "broadcast": {
                        "__ansible_unsafe": "192.168.1.255"
                    },
                    "interface": {
                        "__ansible_unsafe": "vpn0"
                    },
                    "macaddress": {
                        "__ansible_unsafe": ""
                    },
                    "mtu": 1434,
                    "netmask": {
                        "__ansible_unsafe": "255.255.255.0"
                    },
                    "network": {
                        "__ansible_unsafe": "192.168.1.0"
                    },
                    "prefix": {
                        "__ansible_unsafe": "24"
                    },
                    "type": {
                        "__ansible_unsafe": "tunnel"
                    }
                },
                "ansible_default_ipv6": {},
                "ansible_device_links": {
                    "ids": {},
                    "labels": {},
                    "masters": {},
                    "uuids": {}
                },
                "ansible_devices": {
                    "nvme0n1": {
                        "holders": [],
                        "host": {
                            "__ansible_unsafe": ""
                        },
                        "links": {
                            "ids": [],
                            "labels": [],
                            "masters": [],
                            "uuids": []
                        },
                        "model": {
                            "__ansible_unsafe": "WDC PC SN530 SDBPMPZ-512G-1101"
                        },
                        "partitions": {
                            "nvme0n1p1": {
                                "holders": [],
                                "links": {
                                    "ids": [],
                                    "labels": [],
                                    "masters": [],
                                    "uuids": []
                                },
                                "sectors": 1021952,
                                "sectorsize": 512,
                                "size": {
                                    "__ansible_unsafe": "499.00 MB"
                                },
                                "start": {
                                    "__ansible_unsafe": "2048"
                                },
                                "uuid": null
                            },
                            "nvme0n1p2": {
                                "holders": [],
                                "links": {
                                    "ids": [],
                                    "labels": [],
                                    "masters": [],
                                    "uuids": []
                                },
                                "sectors": 2099200,
                                "sectorsize": 512,
                                "size": {
                                    "__ansible_unsafe": "1.00 GB"
                                },
                                "start": {
                                    "__ansible_unsafe": "407500800"
                                },
                                "uuid": null
                            },
                            "nvme0n1p3": {
                                "holders": [],
                                "links": {
                                    "ids": [],
                                    "labels": [],
                                    "masters": [],
                                    "uuids": []
                                },
                                "sectors": 590614528,
                                "sectorsize": 512,
                                "size": {
                                    "__ansible_unsafe": "281.63 GB"
                                },
                                "start": {
                                    "__ansible_unsafe": "409600000"
                                },
                                "uuid": null
                            },
                            "nvme0n1p4": {
                                "holders": [],
                                "links": {
                                    "ids": [],
                                    "labels": [],
                                    "masters": [],
                                    "uuids": []
                                },
                                "sectors": 16777216,
                                "sectorsize": 512,
                                "size": {
                                    "__ansible_unsafe": "8.00 GB"
                                },
                                "start": {
                                    "__ansible_unsafe": "1024000"
                                },
                                "uuid": null
                            },
                            "nvme0n1p5": {
                                "holders": [],
                                "links": {
                                    "ids": [],
                                    "labels": [],
                                    "masters": [],
                                    "uuids": []
                                },
                                "sectors": 209715200,
                                "sectorsize": 512,
                                "size": {
                                    "__ansible_unsafe": "100.00 GB"
                                },
                                "start": {
                                    "__ansible_unsafe": "17801216"
                                },
                                "uuid": null
                            }
                        },
                        "removable": {
                            "__ansible_unsafe": "0"
                        },
                        "rotational": {
                            "__ansible_unsafe": "0"
                        },
                        "sas_address": null,
                        "sas_device_handle": null,
                        "scheduler_mode": {
                            "__ansible_unsafe": "none"
                        },
                        "sectors": 1000215216,
                        "sectorsize": {
                            "__ansible_unsafe": "512"
                        },
                        "serial": {
                            "__ansible_unsafe": "21080F809361"
                        },
                        "size": {
                            "__ansible_unsafe": "476.94 GB"
                        },
                        "support_discard": {
                            "__ansible_unsafe": "512"
                        },
                        "vendor": null,
                        "virtual": 1
                    }
                },
                "ansible_distribution": {
                    "__ansible_unsafe": "Ubuntu"
                },
                "ansible_distribution_file_parsed": true,
                "ansible_distribution_file_path": {
                    "__ansible_unsafe": "/etc/os-release"
                },
                "ansible_distribution_file_variety": {
                    "__ansible_unsafe": "Debian"
                },
                "ansible_distribution_major_version": {
                    "__ansible_unsafe": "20"
                },
                "ansible_distribution_release": {
                    "__ansible_unsafe": "focal"
                },
                "ansible_distribution_version": {
                    "__ansible_unsafe": "20.04"
                },
                "ansible_dns": {
                    "nameservers": [
                        {
                            "__ansible_unsafe": "127.0.0.11"
                        }
                    ],
                    "options": {
                        "ndots": {
                            "__ansible_unsafe": "0"
                        }
                    },
                    "search": [
                        {
                            "__ansible_unsafe": "example.com"
                        }
                    ]
                },
                "ansible_docker0": {
                    "active": true,
                    "device": {
                        "__ansible_unsafe": "docker0"
                    },
                    "id": {
                        "__ansible_unsafe": "8000.024233825e88"
                    },
                    "interfaces": [
                        {
                            "__ansible_unsafe": "veth604322c"
                        }
                    ],
                    "ipv4": {
                        "address": {
                            "__ansible_unsafe": "172.17.0.1"
                        },
                        "broadcast": {
                            "__ansible_unsafe": "172.17.255.255"
                        },
                        "netmask": {
                            "__ansible_unsafe": "255.255.0.0"
                        },
                        "network": {
                            "__ansible_unsafe": "172.17.0.0"
                        },
                        "prefix": {
                            "__ansible_unsafe": "16"
                        }
                    },
                    "ipv6": [
                        {
                            "address": {
                                "__ansible_unsafe": "fe80::42:33ff:fe82:5e88"
                            },
                            "prefix": {
                                "__ansible_unsafe": "64"
                            },
                            "scope": {
                                "__ansible_unsafe": "link"
                            }
                        }
                    ],
                    "macaddress": {
                        "__ansible_unsafe": "02:42:33:82:5e:88"
                    },
                    "mtu": 1500,
                    "promisc": false,
                    "speed": 10000,
                    "stp": false,
                    "type": {
                        "__ansible_unsafe": "bridge"
                    }
                },
                "ansible_domain": {
                    "__ansible_unsafe": ""
                },
                "ansible_effective_group_id": 0,
                "ansible_effective_user_id": 0,
                "ansible_env": {
                    "HOME": {
                        "__ansible_unsafe": "/root"
                    },
                    "LC_CTYPE": {
                        "__ansible_unsafe": "C.UTF-8"
                    },
                    "LOGNAME": {
                        "__ansible_unsafe": "root"
                    },
                    "MOTD_SHOWN": {
                        "__ansible_unsafe": "pam"
                    },
                    "PATH": {
                        "__ansible_unsafe": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"
                    },
                    "PWD": {
                        "__ansible_unsafe": "/root"
                    },
                    "SHELL": {
                        "__ansible_unsafe": "/bin/bash"
                    },
                    "SHLVL": {
                        "__ansible_unsafe": "0"
                    },
                    "SSH_CLIENT": {
                        "__ansible_unsafe": "172.19.0.1 53768 22"
                    },
                    "SSH_CONNECTION": {
                        "__ansible_unsafe": "172.19.0.1 53768 172.19.0.2 22"
                    },
                    "SSH_TTY": {
                        "__ansible_unsafe": "/dev/pts/0"
                    },
                    "TERM": {
                        "__ansible_unsafe": "tmux-256color"
                    },
                    "USER": {
                        "__ansible_unsafe": "root"
                    },
                    "_": {
                        "__ansible_unsafe": "/bin/sh"
                    }
                },
                "ansible_fibre_channel_wwn": [],
                "ansible_fips": false,
                "ansible_flags": [
                    {
                        "__ansible_unsafe": "fpu"
                    },
                    {
                        "__ansible_unsafe": "vme"
                    },
                    {
                        "__ansible_unsafe": "de"
                    },
                    {
                        "__ansible_unsafe": "pse"
                    },
                    {
                        "__ansible_unsafe": "tsc"
                    },
                    {
                        "__ansible_unsafe": "msr"
                    },
                    {
                        "__ansible_unsafe": "pae"
                    },
                    {
                        "__ansible_unsafe": "mce"
                    },
                    {
                        "__ansible_unsafe": "cx8"
                    },
                    {
                        "__ansible_unsafe": "apic"
                    },
                    {
                        "__ansible_unsafe": "sep"
                    },
                    {
                        "__ansible_unsafe": "mtrr"
                    },
                    {
                        "__ansible_unsafe": "pge"
                    },
                    {
                        "__ansible_unsafe": "mca"
                    },
                    {
                        "__ansible_unsafe": "cmov"
                    },
                    {
                        "__ansible_unsafe": "pat"
                    },
                    {
                        "__ansible_unsafe": "pse36"
                    },
                    {
                        "__ansible_unsafe": "clflush"
                    },
                    {
                        "__ansible_unsafe": "mmx"
                    },
                    {
                        "__ansible_unsafe": "fxsr"
                    },
                    {
                        "__ansible_unsafe": "sse"
                    },
                    {
                        "__ansible_unsafe": "sse2"
                    },
                    {
                        "__ansible_unsafe": "ht"
                    },
                    {
                        "__ansible_unsafe": "syscall"
                    },
                    {
                        "__ansible_unsafe": "nx"
                    },
                    {
                        "__ansible_unsafe": "mmxext"
                    },
                    {
                        "__ansible_unsafe": "fxsr_opt"
                    },
                    {
                        "__ansible_unsafe": "pdpe1gb"
                    },
                    {
                        "__ansible_unsafe": "rdtscp"
                    },
                    {
                        "__ansible_unsafe": "lm"
                    },
                    {
                        "__ansible_unsafe": "constant_tsc"
                    },
                    {
                        "__ansible_unsafe": "rep_good"
                    },
                    {
                        "__ansible_unsafe": "nopl"
                    },
                    {
                        "__ansible_unsafe": "xtopology"
                    },
                    {
                        "__ansible_unsafe": "nonstop_tsc"
                    },
                    {
                        "__ansible_unsafe": "cpuid"
                    },
                    {
                        "__ansible_unsafe": "extd_apicid"
                    },
                    {
                        "__ansible_unsafe": "aperfmperf"
                    },
                    {
                        "__ansible_unsafe": "rapl"
                    },
                    {
                        "__ansible_unsafe": "pni"
                    },
                    {
                        "__ansible_unsafe": "pclmulqdq"
                    },
                    {
                        "__ansible_unsafe": "monitor"
                    },
                    {
                        "__ansible_unsafe": "ssse3"
                    },
                    {
                        "__ansible_unsafe": "fma"
                    },
                    {
                        "__ansible_unsafe": "cx16"
                    },
                    {
                        "__ansible_unsafe": "sse4_1"
                    },
                    {
                        "__ansible_unsafe": "sse4_2"
                    },
                    {
                        "__ansible_unsafe": "movbe"
                    },
                    {
                        "__ansible_unsafe": "popcnt"
                    },
                    {
                        "__ansible_unsafe": "aes"
                    },
                    {
                        "__ansible_unsafe": "xsave"
                    },
                    {
                        "__ansible_unsafe": "avx"
                    },
                    {
                        "__ansible_unsafe": "f16c"
                    },
                    {
                        "__ansible_unsafe": "rdrand"
                    },
                    {
                        "__ansible_unsafe": "lahf_lm"
                    },
                    {
                        "__ansible_unsafe": "cmp_legacy"
                    },
                    {
                        "__ansible_unsafe": "svm"
                    },
                    {
                        "__ansible_unsafe": "extapic"
                    },
                    {
                        "__ansible_unsafe": "cr8_legacy"
                    },
                    {
                        "__ansible_unsafe": "abm"
                    },
                    {
                        "__ansible_unsafe": "sse4a"
                    },
                    {
                        "__ansible_unsafe": "misalignsse"
                    },
                    {
                        "__ansible_unsafe": "3dnowprefetch"
                    },
                    {
                        "__ansible_unsafe": "osvw"
                    },
                    {
                        "__ansible_unsafe": "ibs"
                    },
                    {
                        "__ansible_unsafe": "skinit"
                    },
                    {
                        "__ansible_unsafe": "wdt"
                    },
                    {
                        "__ansible_unsafe": "tce"
                    },
                    {
                        "__ansible_unsafe": "topoext"
                    },
                    {
                        "__ansible_unsafe": "perfctr_core"
                    },
                    {
                        "__ansible_unsafe": "perfctr_nb"
                    },
                    {
                        "__ansible_unsafe": "bpext"
                    },
                    {
                        "__ansible_unsafe": "perfctr_llc"
                    },
                    {
                        "__ansible_unsafe": "mwaitx"
                    },
                    {
                        "__ansible_unsafe": "cpb"
                    },
                    {
                        "__ansible_unsafe": "cat_l3"
                    },
                    {
                        "__ansible_unsafe": "cdp_l3"
                    },
                    {
                        "__ansible_unsafe": "hw_pstate"
                    },
                    {
                        "__ansible_unsafe": "ssbd"
                    },
                    {
                        "__ansible_unsafe": "mba"
                    },
                    {
                        "__ansible_unsafe": "ibrs"
                    },
                    {
                        "__ansible_unsafe": "ibpb"
                    },
                    {
                        "__ansible_unsafe": "stibp"
                    },
                    {
                        "__ansible_unsafe": "vmmcall"
                    },
                    {
                        "__ansible_unsafe": "fsgsbase"
                    },
                    {
                        "__ansible_unsafe": "bmi1"
                    },
                    {
                        "__ansible_unsafe": "avx2"
                    },
                    {
                        "__ansible_unsafe": "smep"
                    },
                    {
                        "__ansible_unsafe": "bmi2"
                    },
                    {
                        "__ansible_unsafe": "cqm"
                    },
                    {
                        "__ansible_unsafe": "rdt_a"
                    },
                    {
                        "__ansible_unsafe": "rdseed"
                    },
                    {
                        "__ansible_unsafe": "adx"
                    },
                    {
                        "__ansible_unsafe": "smap"
                    },
                    {
                        "__ansible_unsafe": "clflushopt"
                    },
                    {
                        "__ansible_unsafe": "clwb"
                    },
                    {
                        "__ansible_unsafe": "sha_ni"
                    },
                    {
                        "__ansible_unsafe": "xsaveopt"
                    },
                    {
                        "__ansible_unsafe": "xsavec"
                    },
                    {
                        "__ansible_unsafe": "xgetbv1"
                    },
                    {
                        "__ansible_unsafe": "cqm_llc"
                    },
                    {
                        "__ansible_unsafe": "cqm_occup_llc"
                    },
                    {
                        "__ansible_unsafe": "cqm_mbm_total"
                    },
                    {
                        "__ansible_unsafe": "cqm_mbm_local"
                    },
                    {
                        "__ansible_unsafe": "clzero"
                    },
                    {
                        "__ansible_unsafe": "irperf"
                    },
                    {
                        "__ansible_unsafe": "xsaveerptr"
                    },
                    {
                        "__ansible_unsafe": "rdpru"
                    },
                    {
                        "__ansible_unsafe": "wbnoinvd"
                    },
                    {
                        "__ansible_unsafe": "cppc"
                    },
                    {
                        "__ansible_unsafe": "arat"
                    },
                    {
                        "__ansible_unsafe": "npt"
                    },
                    {
                        "__ansible_unsafe": "lbrv"
                    },
                    {
                        "__ansible_unsafe": "svm_lock"
                    },
                    {
                        "__ansible_unsafe": "nrip_save"
                    },
                    {
                        "__ansible_unsafe": "tsc_scale"
                    },
                    {
                        "__ansible_unsafe": "vmcb_clean"
                    },
                    {
                        "__ansible_unsafe": "flushbyasid"
                    },
                    {
                        "__ansible_unsafe": "decodeassists"
                    },
                    {
                        "__ansible_unsafe": "pausefilter"
                    },
                    {
                        "__ansible_unsafe": "pfthreshold"
                    },
                    {
                        "__ansible_unsafe": "avic"
                    },
                    {
                        "__ansible_unsafe": "v_vmsave_vmload"
                    },
                    {
                        "__ansible_unsafe": "vgif"
                    },
                    {
                        "__ansible_unsafe": "v_spec_ctrl"
                    },
                    {
                        "__ansible_unsafe": "umip"
                    },
                    {
                        "__ansible_unsafe": "rdpid"
                    },
                    {
                        "__ansible_unsafe": "overflow_recov"
                    },
                    {
                        "__ansible_unsafe": "succor"
                    },
                    {
                        "__ansible_unsafe": "smca"
                    }
                ],
                "ansible_form_factor": {
                    "__ansible_unsafe": "Notebook"
                },
                "ansible_fqdn": {
                    "__ansible_unsafe": "536c1046eb9d"
                },
                "ansible_host": "127.0.0.1",
                "ansible_hostname": {
                    "__ansible_unsafe": "536c1046eb9d"
                },
                "ansible_hostnqn": {
                    "__ansible_unsafe": ""
                },
                "ansible_interfaces": [
                    {
                        "__ansible_unsafe": "docker0"
                    },
                    {
                        "__ansible_unsafe": "br-8cfa35c2750f"
                    },
                    {
                        "__ansible_unsafe": "wlan0"
                    },
                    {
                        "__ansible_unsafe": "vpn0"
                    },
                    {
                        "__ansible_unsafe": "veth604322c"
                    },
                    {
                        "__ansible_unsafe": "ztfp6i74v5"
                    },
                    {
                        "__ansible_unsafe": "lo"
                    }
                ],
                "ansible_is_chroot": false,
                "ansible_iscsi_iqn": {
                    "__ansible_unsafe": ""
                },
                "ansible_kernel": {
                    "__ansible_unsafe": "6.12.10-arch1-1"
                },
                "ansible_kernel_version": {
                    "__ansible_unsafe": "#1 SMP PREEMPT_DYNAMIC Sat, 18 Jan 2025 02:26:57 +0000"
                },
                "ansible_lo": {
                    "active": true,
                    "device": {
                        "__ansible_unsafe": "lo"
                    },
                    "ipv4": {
                        "address": {
                            "__ansible_unsafe": "127.0.0.1"
                        },
                        "broadcast": {
                            "__ansible_unsafe": ""
                        },
                        "netmask": {
                            "__ansible_unsafe": "255.0.0.0"
                        },
                        "network": {
                            "__ansible_unsafe": "127.0.0.0"
                        },
                        "prefix": {
                            "__ansible_unsafe": "8"
                        }
                    },
                    "ipv6": [
                        {
                            "address": {
                                "__ansible_unsafe": "::1"
                            },
                            "prefix": {
                                "__ansible_unsafe": "128"
                            },
                            "scope": {
                                "__ansible_unsafe": "host"
                            }
                        }
                    ],
                    "mtu": 65536,
                    "promisc": false,
                    "type": {
                        "__ansible_unsafe": "loopback"
                    }
                },
                "ansible_loadavg": {
                    "15m": 1.21,
                    "1m": 1.85,
                    "5m": 1.62
                },
                "ansible_local": {},
                "ansible_locally_reachable_ips": {
                    "ipv4": [
                        {
                            "__ansible_unsafe": "10.91.51.42"
                        },
                        {
                            "__ansible_unsafe": "10.244.53.78"
                        },
                        {
                            "__ansible_unsafe": "127.0.0.0/8"
                        },
                        {
                            "__ansible_unsafe": "127.0.0.1"
                        },
                        {
                            "__ansible_unsafe": "172.17.0.1"
                        },
                        {
                            "__ansible_unsafe": "172.18.0.1"
                        },
                        {
                            "__ansible_unsafe": "192.168.1.160"
                        }
                    ],
                    "ipv6": [
                        {
                            "__ansible_unsafe": "::1"
                        },
                        {
                            "__ansible_unsafe": "fe80::42:33ff:fe82:5e88"
                        },
                        {
                            "__ansible_unsafe": "fe80::5c2a:7aff:fe90:53ad"
                        },
                        {
                            "__ansible_unsafe": "fe80::9eaa:991c:ae5a:7c1e"
                        },
                        {
                            "__ansible_unsafe": "fe80::f09a:67ff:fec1:efad"
                        }
                    ]
                },
                "ansible_lsb": {
                    "codename": {
                        "__ansible_unsafe": "focal"
                    },
                    "description": {
                        "__ansible_unsafe": "Ubuntu 20.04.6 LTS"
                    },
                    "id": {
                        "__ansible_unsafe": "Ubuntu"
                    },
                    "major_release": {
                        "__ansible_unsafe": "20"
                    },
                    "release": {
                        "__ansible_unsafe": "20.04"
                    }
                },
                "ansible_lvm": {
                    "__ansible_unsafe": "N/A"
                },
                "ansible_machine": {
                    "__ansible_unsafe": "x86_64"
                },
                "ansible_machine_id": {
                    "__ansible_unsafe": "cf33a99bf95449f9a7898cbe30a23777"
                },
                "ansible_memfree_mb": 941,
                "ansible_memory_mb": {
                    "nocache": {
                        "free": 2188,
                        "used": 5097
                    },
                    "real": {
                        "free": 941,
                        "total": 7285,
                        "used": 6344
                    },
                    "swap": {
                        "cached": 240,
                        "free": 5019,
                        "total": 8191,
                        "used": 3172
                    }
                },
                "ansible_memtotal_mb": 7285,
                "ansible_mounts": [
                    {
                        "block_available": 403038,
                        "block_size": 4096,
                        "block_total": 25656558,
                        "block_used": 25253520,
                        "device": {
                            "__ansible_unsafe": "/dev/nvme0n1p5"
                        },
                        "dump": 0,
                        "fstype": {
                            "__ansible_unsafe": "ext4"
                        },
                        "inode_available": 5014028,
                        "inode_total": 6553600,
                        "inode_used": 1539572,
                        "mount": {
                            "__ansible_unsafe": "/etc/resolv.conf"
                        },
                        "options": {
                            "__ansible_unsafe": "rw,relatime,bind"
                        },
                        "passno": 0,
                        "size_available": 1650843648,
                        "size_total": 105089261568,
                        "uuid": {
                            "__ansible_unsafe": "N/A"
                        }
                    },
                    {
                        "block_available": 403038,
                        "block_size": 4096,
                        "block_total": 25656558,
                        "block_used": 25253520,
                        "device": {
                            "__ansible_unsafe": "/dev/nvme0n1p5"
                        },
                        "dump": 0,
                        "fstype": {
                            "__ansible_unsafe": "ext4"
                        },
                        "inode_available": 5014028,
                        "inode_total": 6553600,
                        "inode_used": 1539572,
                        "mount": {
                            "__ansible_unsafe": "/etc/hostname"
                        },
                        "options": {
                            "__ansible_unsafe": "rw,relatime,bind"
                        },
                        "passno": 0,
                        "size_available": 1650843648,
                        "size_total": 105089261568,
                        "uuid": {
                            "__ansible_unsafe": "N/A"
                        }
                    },
                    {
                        "block_available": 403038,
                        "block_size": 4096,
                        "block_total": 25656558,
                        "block_used": 25253520,
                        "device": {
                            "__ansible_unsafe": "/dev/nvme0n1p5"
                        },
                        "dump": 0,
                        "fstype": {
                            "__ansible_unsafe": "ext4"
                        },
                        "inode_available": 5014028,
                        "inode_total": 6553600,
                        "inode_used": 1539572,
                        "mount": {
                            "__ansible_unsafe": "/etc/hosts"
                        },
                        "options": {
                            "__ansible_unsafe": "rw,relatime,bind"
                        },
                        "passno": 0,
                        "size_available": 1650843648,
                        "size_total": 105089261568,
                        "uuid": {
                            "__ansible_unsafe": "N/A"
                        }
                    }
                ],
                "ansible_nodename": {
                    "__ansible_unsafe": "536c1046eb9d"
                },
                "ansible_os_family": {
                    "__ansible_unsafe": "Debian"
                },
                "ansible_password": "rootpassword",
                "ansible_pkg_mgr": {
                    "__ansible_unsafe": "apt"
                },
                "ansible_port": 22,
                "ansible_proc_cmdline": {
                    "BOOT_IMAGE": {
                        "__ansible_unsafe": "/vmlinuz-linux"
                    },
                    "loglevel": {
                        "__ansible_unsafe": "3"
                    },
                    "quiet": true,
                    "root": {
                        "__ansible_unsafe": "UUID=cf7c794f-dad7-4c4b-a880-3fe6c388b903"
                    },
                    "rw": true
                },
                "ansible_processor": [
                    {
                        "__ansible_unsafe": "0"
                    },
                    {
                        "__ansible_unsafe": "AuthenticAMD"
                    },
                    {
                        "__ansible_unsafe": "AMD Ryzen 3 5300U with Radeon Graphics"
                    },
                    {
                        "__ansible_unsafe": "1"
                    },
                    {
                        "__ansible_unsafe": "AuthenticAMD"
                    },
                    {
                        "__ansible_unsafe": "AMD Ryzen 3 5300U with Radeon Graphics"
                    },
                    {
                        "__ansible_unsafe": "2"
                    },
                    {
                        "__ansible_unsafe": "AuthenticAMD"
                    },
                    {
                        "__ansible_unsafe": "AMD Ryzen 3 5300U with Radeon Graphics"
                    },
                    {
                        "__ansible_unsafe": "3"
                    },
                    {
                        "__ansible_unsafe": "AuthenticAMD"
                    },
                    {
                        "__ansible_unsafe": "AMD Ryzen 3 5300U with Radeon Graphics"
                    },
                    {
                        "__ansible_unsafe": "4"
                    },
                    {
                        "__ansible_unsafe": "AuthenticAMD"
                    },
                    {
                        "__ansible_unsafe": "AMD Ryzen 3 5300U with Radeon Graphics"
                    },
                    {
                        "__ansible_unsafe": "5"
                    },
                    {
                        "__ansible_unsafe": "AuthenticAMD"
                    },
                    {
                        "__ansible_unsafe": "AMD Ryzen 3 5300U with Radeon Graphics"
                    },
                    {
                        "__ansible_unsafe": "6"
                    },
                    {
                        "__ansible_unsafe": "AuthenticAMD"
                    },
                    {
                        "__ansible_unsafe": "AMD Ryzen 3 5300U with Radeon Graphics"
                    },
                    {
                        "__ansible_unsafe": "7"
                    },
                    {
                        "__ansible_unsafe": "AuthenticAMD"
                    },
                    {
                        "__ansible_unsafe": "AMD Ryzen 3 5300U with Radeon Graphics"
                    }
                ],
                "ansible_processor_cores": 4,
                "ansible_processor_count": 1,
                "ansible_processor_nproc": 8,
                "ansible_processor_threads_per_core": 2,
                "ansible_processor_vcpus": 8,
                "ansible_product_name": {
                    "__ansible_unsafe": "82LM"
                },
                "ansible_product_serial": {
                    "__ansible_unsafe": "MP1ZS5RF"
                },
                "ansible_product_uuid": {
                    "__ansible_unsafe": "4a1cfbfa-8886-11eb-810a-7c8ae174deb8"
                },
                "ansible_product_version": {
                    "__ansible_unsafe": "IdeaPad 5 14ALC05"
                },
                "ansible_python": {
                    "executable": {
                        "__ansible_unsafe": "/usr/bin/python3"
                    },
                    "has_sslcontext": true,
                    "type": {
                        "__ansible_unsafe": "cpython"
                    },
                    "version": {
                        "major": 3,
                        "micro": 10,
                        "minor": 8,
                        "releaselevel": {
                            "__ansible_unsafe": "final"
                        },
                        "serial": 0
                    },
                    "version_info": [
                        3,
                        8,
                        10,
                        {
                            "__ansible_unsafe": "final"
                        },
                        0
                    ]
                },
                "ansible_python_interpreter": "/usr/bin/python3",
                "ansible_python_version": {
                    "__ansible_unsafe": "3.8.10"
                },
                "ansible_real_group_id": 0,
                "ansible_real_user_id": 0,
                "ansible_selinux": {
                    "status": {
                        "__ansible_unsafe": "disabled"
                    }
                },
                "ansible_selinux_python_present": true,
                "ansible_service_mgr": {
                    "__ansible_unsafe": "sshd"
                },
                "ansible_ssh_host_key_ecdsa_public": {
                    "__ansible_unsafe": "AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBB/GNPRHKV2Mav4mr7ytJzMP65r45K12XMlx2uixWZaE7jAuL9O5RhUDvbdohompoZX4LSu0GBBxHKLJ/rXRidM="
                },
                "ansible_ssh_host_key_ecdsa_public_keytype": {
                    "__ansible_unsafe": "ecdsa-sha2-nistp256"
                },
                "ansible_ssh_host_key_ed25519_public": {
                    "__ansible_unsafe": "AAAAC3NzaC1lZDI1NTE5AAAAIJb4hnhRBTfezHV9vBQXdLEnF8brvXxl63vhtGTXc3o1"
                },
                "ansible_ssh_host_key_ed25519_public_keytype": {
                    "__ansible_unsafe": "ssh-ed25519"
                },
                "ansible_ssh_host_key_rsa_public": {
                    "__ansible_unsafe": "AAAAB3NzaC1yc2EAAAADAQABAAABgQDc3iYIFSctKLNcdZpFveDSJ7QL3J+H0CMkikbm44G/pSZYV41/HizFZmLB+P5Mq32DVoRqHyt/t99NYn2snnPQWn/J8xDkzrGNodprabYAoe4B6L21IX3lOQJ+kp3F0dkVItNjmsApNmlt5caW2DGRWlxp5EsqdFJnysma6ssZGWReRGxaMmGOQZ/h0hEHPFUMhAjjquP/Efgs02cDDAiwuDEo5p571ChmW/bA26oG0ARTTta6JRPxfxraQP7u8NWQT4EGud4LZz8exFVD1xJZosPQWztZ5tajjWsgLAf/42nZgCLPbJf0sxv3/3crYB9k7SKrFs2HIOLYBSbbbrBdKM6v1S4waJfJCXSudIuue4cpKK96lE5s2IkDX8UdGYEeX+tQ6j4MOmxoOmqEuum//4s7d5KrviczsF2xNU4faaiNp1VJmtw10R49XKo8nzKwxMMmqT83SRS2sB3MfLshkqWl4+F1A4jllgmrUiE/7nNHvIHStpg4lWI3j9CCUkc="
                },
                "ansible_ssh_host_key_rsa_public_keytype": {
                    "__ansible_unsafe": "ssh-rsa"
                },
                "ansible_swapfree_mb": 5019,
                "ansible_swaptotal_mb": 8191,
                "ansible_system": {
                    "__ansible_unsafe": "Linux"
                },
                "ansible_system_capabilities": [],
                "ansible_system_capabilities_enforced": {
                    "__ansible_unsafe": "False"
                },
                "ansible_system_vendor": {
                    "__ansible_unsafe": "LENOVO"
                },
                "ansible_systemd": {
                    "features": {
                        "__ansible_unsafe": "+PAM +AUDIT -SELINUX -APPARMOR -IMA +IPE +SMACK +SECCOMP +GCRYPT +GNUTLS +OPENSSL +ACL +BLKID +CURL +ELFUTILS +FIDO2 +IDN2 -IDN +IPTC +KMOD +LIBCRYPTSETUP +LIBCRYPTSETUP_PLUGINS +LIBFDISK +PCRE2 +PWQUALITY +P11KIT +QRENCODE +TPM2 +BZIP2 +LZ4 +XZ +ZLIB +ZSTD +BPF_FRAMEWORK +BTF +XKBCOMMON +UTMP -SYSVINIT +LIBARCHIVE"
                    },
                    "version": 257
                },
                "ansible_uptime_seconds": 514838,
                "ansible_user": "root",
                "ansible_user_dir": {
                    "__ansible_unsafe": "/root"
                },
                "ansible_user_gecos": {
                    "__ansible_unsafe": "root"
                },
                "ansible_user_gid": 0,
                "ansible_user_id": {
                    "__ansible_unsafe": "root"
                },
                "ansible_user_shell": {
                    "__ansible_unsafe": "/bin/bash"
                },
                "ansible_user_uid": 0,
                "ansible_userspace_architecture": {
                    "__ansible_unsafe": "x86_64"
                },
                "ansible_userspace_bits": {
                    "__ansible_unsafe": "64"
                },
                "ansible_veth604322c": {
                    "active": true,
                    "device": {
                        "__ansible_unsafe": "veth604322c"
                    },
                    "ipv6": [
                        {
                            "address": {
                                "__ansible_unsafe": "fe80::5c2a:7aff:fe90:53ad"
                            },
                            "prefix": {
                                "__ansible_unsafe": "64"
                            },
                            "scope": {
                                "__ansible_unsafe": "link"
                            }
                        }
                    ],
                    "macaddress": {
                        "__ansible_unsafe": "5e:2a:7a:90:53:ad"
                    },
                    "mtu": 1500,
                    "promisc": true,
                    "speed": 10000,
                    "type": {
                        "__ansible_unsafe": "ether"
                    }
                },
                "ansible_virtualization_role": {
                    "__ansible_unsafe": "guest"
                },
                "ansible_virtualization_tech_guest": [
                    {
                        "__ansible_unsafe": "docker"
                    },
                    {
                        "__ansible_unsafe": "container"
                    }
                ],
                "ansible_virtualization_tech_host": [
                    {
                        "__ansible_unsafe": "kvm"
                    }
                ],
                "ansible_virtualization_type": {
                    "__ansible_unsafe": "docker"
                },
                "ansible_vpn0": {
                    "active": true,
                    "device": {
                        "__ansible_unsafe": "vpn0"
                    },
                    "ipv4": {
                        "address": {
                            "__ansible_unsafe": "192.168.1.160"
                        },
                        "broadcast": {
                            "__ansible_unsafe": "192.168.1.255"
                        },
                        "netmask": {
                            "__ansible_unsafe": "255.255.255.0"
                        },
                        "network": {
                            "__ansible_unsafe": "192.168.1.0"
                        },
                        "prefix": {
                            "__ansible_unsafe": "24"
                        }
                    },
                    "mtu": 1434,
                    "promisc": false,
                    "speed": 10000,
                    "type": {
                        "__ansible_unsafe": "tunnel"
                    }
                },
                "ansible_wlan0": {
                    "active": true,
                    "device": {
                        "__ansible_unsafe": "wlan0"
                    },
                    "ipv4": {
                        "address": {
                            "__ansible_unsafe": "10.91.51.42"
                        },
                        "broadcast": {
                            "__ansible_unsafe": "10.91.63.255"
                        },
                        "netmask": {
                            "__ansible_unsafe": "255.255.240.0"
                        },
                        "network": {
                            "__ansible_unsafe": "10.91.48.0"
                        },
                        "prefix": {
                            "__ansible_unsafe": "20"
                        }
                    },
                    "ipv6": [
                        {
                            "address": {
                                "__ansible_unsafe": "fe80::9eaa:991c:ae5a:7c1e"
                            },
                            "prefix": {
                                "__ansible_unsafe": "64"
                            },
                            "scope": {
                                "__ansible_unsafe": "link"
                            }
                        }
                    ],
                    "macaddress": {
                        "__ansible_unsafe": "c0:3c:59:aa:1d:24"
                    },
                    "module": {
                        "__ansible_unsafe": "iwlwifi"
                    },
                    "mtu": 1500,
                    "pciid": {
                        "__ansible_unsafe": "0000:03:00.0"
                    },
                    "promisc": false,
                    "type": {
                        "__ansible_unsafe": "ether"
                    }
                },
                "ansible_ztfp6i74v5": {
                    "active": true,
                    "device": {
                        "__ansible_unsafe": "ztfp6i74v5"
                    },
                    "ipv4": {
                        "address": {
                            "__ansible_unsafe": "10.244.53.78"
                        },
                        "broadcast": {
                            "__ansible_unsafe": "10.244.255.255"
                        },
                        "netmask": {
                            "__ansible_unsafe": "255.255.0.0"
                        },
                        "network": {
                            "__ansible_unsafe": "10.244.0.0"
                        },
                        "prefix": {
                            "__ansible_unsafe": "16"
                        }
                    },
                    "ipv6": [
                        {
                            "address": {
                                "__ansible_unsafe": "fe80::f09a:67ff:fec1:efad"
                            },
                            "prefix": {
                                "__ansible_unsafe": "64"
                            },
                            "scope": {
                                "__ansible_unsafe": "link"
                            }
                        }
                    ],
                    "macaddress": {
                        "__ansible_unsafe": "f2:9a:67:c1:ef:ad"
                    },
                    "mtu": 2800,
                    "promisc": false,
                    "speed": 10000,
                    "type": {
                        "__ansible_unsafe": "ether"
                    }
                },
                "gather_subset": [
                    {
                        "__ansible_unsafe": "all"
                    }
                ],
                "module_setup": true
            }
        }
    },
    "all": {
        "children": [
            "ungrouped"
        ]
    },
    "ungrouped": {
        "hosts": [
            "test_host"
        ]
    }
}

```

### ansible inventory graph

```
@all:
  |--@ungrouped:
  |  |--test_host
```

## Lab 6

### deploy app_python

```bash
ansible-playbook -i inventory/local.yml playbooks/dev/app_python.yaml


~ ansible-playbook -i inventory/local.yml playbooks/dev/app_python.yaml

TASK [docker : Configure Docker daemon security] ********************************************************************************************************************************
ok: [test_host]

TASK [docker : Detect init system] **********************************************************************************************************************************************
ok: [test_host]

TASK [docker : Enable Docker service (Systemd only)] ****************************************************************************************************************************
skipping: [test_host]

TASK [docker : Restart Docker (Systemd only)] ***********************************************************************************************************************************
skipping: [test_host]

TASK [docker : Restart Docker (Service)] ****************************************************************************************************************************************
changed: [test_host]

TASK [web_app : Check if Docker is installed] ***********************************************************************************************************************************
ok: [test_host]

TASK [web_app : Fail if Docker is not installed] ********************************************************************************************************************************
skipping: [test_host]

TASK [web_app : Create app directory] *******************************************************************************************************************************************
changed: [test_host]

TASK [web_app : Copy Docker Compose template] ***********************************************************************************************************************************
changed: [test_host]

TASK [web_app : Ensure docker service is active] ********************************************************************************************************************************
changed: [test_host]

TASK [web_app : Create and start the application services] **********************************************************************************************************************
changed: [test_host]

TASK [web_app : Check if web app directory exists] ******************************************************************************************************************************
skipping: [test_host]

TASK [web_app : Stop and remove the web app container] **************************************************************************************************************************
skipping: [test_host]

TASK [web_app : Remove app sources] *********************************************************************************************************************************************
skipping: [test_host]

PLAY RECAP **********************************************************************************************************************************************************************
test_host                  : ok=19   changed=5    unreachable=0    failed=0    skipped=6    rescued=0    ignored=0
```
