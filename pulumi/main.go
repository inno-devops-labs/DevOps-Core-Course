package main

import (
	"fmt"
	"os"

	"github.com/pulumi/pulumi-yandex/sdk/go/yandex"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi/config"
)

func main() {
	pulumi.Run(func(ctx *pulumi.Context) error {
		cfg := config.New(ctx, "")

		cloudID := cfg.Require("cloud_id")
		folderID := cfg.Require("folder_id")
		zone := cfg.Get("zone")
		if zone == "" {
			zone = "ru-central1-a"
		}
		myIP := cfg.Require("my_ip")

		network, err := yandex.NewVpcNetwork(ctx, "network", &yandex.VpcNetworkArgs{
			Name:     pulumi.String("myapp-network"),
			FolderId: pulumi.String(folderID),
		})
		if err != nil {
			return err
		}

		subnet, err := yandex.NewVpcSubnet(ctx, "subnet", &yandex.VpcSubnetArgs{
			Name:         pulumi.String("myapp-subnet"),
			Zone:         pulumi.String(zone),
			NetworkId:    network.ID(),
			V4CidrBlocks: pulumi.StringArray{pulumi.String("192.168.10.0/24")},
			FolderId:     pulumi.String(folderID),
		})
		if err != nil {
			return err
		}

		sshKey, err := os.ReadFile("/home/bulatgazizov/.ssh/id_rsa.pub")
		if err != nil {
			return err
		}

		userData := fmt.Sprintf(`#cloud-config
runcmd:
  - iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
  - iptables -A INPUT -i lo -j ACCEPT
  - iptables -A INPUT -p tcp --dport 22 -s %s/32 -j ACCEPT
  - iptables -A INPUT -p tcp --dport 80 -j ACCEPT
  - iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
  - iptables -A INPUT -j DROP
  - apt-get install -y iptables-persistent
  - netfilter-persistent save
`, myIP)

		// VM
		vm, err := yandex.NewComputeInstance(ctx, "vm", &yandex.ComputeInstanceArgs{
			Name:     pulumi.String("myapp-vm"),
			Zone:     pulumi.String(zone),
			FolderId: pulumi.String(folderID),
			Resources: &yandex.ComputeInstanceResourcesArgs{
				Cores:        pulumi.Int(2),
				Memory:       pulumi.Float64(1),
				CoreFraction: pulumi.Int(5),
			},
			BootDisk: &yandex.ComputeInstanceBootDiskArgs{
				InitializeParams: &yandex.ComputeInstanceBootDiskInitializeParamsArgs{
					ImageId: pulumi.String("fd84mnbiarffhtfrhnog"),
					Size:    pulumi.Int(20),
					Type:    pulumi.String("network-hdd"),
				},
			},
			NetworkInterfaces: yandex.ComputeInstanceNetworkInterfaceArray{
				&yandex.ComputeInstanceNetworkInterfaceArgs{
					SubnetId: subnet.ID(),
					Nat:      pulumi.Bool(true),
				},
			},
			Metadata: pulumi.StringMap{
				"ssh-keys":  pulumi.String("ubuntu:" + string(sshKey)),
				"user-data": pulumi.String(userData),
			},
		})
		if err != nil {
			return err
		}

		ctx.Export("vm_id", vm.ID())
		ctx.Export("vm_public_ip", vm.NetworkInterfaces.Index(pulumi.Int(0)).NatIpAddress())
		ctx.Export("ssh_command", vm.NetworkInterfaces.Index(pulumi.Int(0)).NatIpAddress().ApplyT(
			func(ip *string) string { return ("ssh ubuntu@" + *ip) },
		).(pulumi.StringOutput))

		_ = cloudID
		return nil
	})
}
