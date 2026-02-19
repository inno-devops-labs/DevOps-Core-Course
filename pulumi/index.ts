import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const config = new pulumi.Config();
const sshKeyName = config.require("ssh_key_name");

const region = "eu-north-1";
const awsConfig = new pulumi.Config("aws");
awsConfig.region = region;

const sshGroup = new aws.ec2.SecurityGroup("ubuntu-ssh", {
  ingress: [{
    protocol: "tcp",
    fromPort: 22,
    toPort: 22,
    cidrBlocks: ["0.0.0.0/0"],
  }],
  egress: [{
    protocol: "-1",
    fromPort: 0,
    toPort: 0,
    cidrBlocks: ["0.0.0.0/0"],
  }],
});

const vm = new aws.ec2.Instance("ubuntu-vm", {
  instanceType: "t3.micro",
  ami: "ami-0974a2c5ddf10f442",
  keyName: sshKeyName,
  vpcSecurityGroupIds: [sshGroup.id],
  associatePublicIpAddress: true,
  tags: {
    Name: "ubuntu-vm",
  },
});

export const publicIp = vm.publicIp;
