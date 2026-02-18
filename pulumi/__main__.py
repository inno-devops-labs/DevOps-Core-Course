import pulumi
from pulumi.dynamic import Resource, ResourceProvider, CreateResult

class VPSProvider(ResourceProvider):
    def create(self, props):
        import subprocess
        commands = [
            "systemctl restart nginx",
            "echo 'Lab04 VPS configured by Pulumi' > /var/www/html/index.html"
        ]
        for cmd in commands:
            result = subprocess.run([
                "ssh",
                "-i", props["private_key_path"],
                "-o", "StrictHostKeyChecking=no",
                f"{props['user']}@{props['host']}",
                cmd
            ], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Command failed: {cmd}\n{result.stderr}")
        return CreateResult(id_="vps-pulumi", outs=props)

class VPSResource(Resource):
    def __init__(self, name, host, user, private_key_path, opts=None):
        super().__init__(VPSProvider(), name, {
            "host": host,
            "user": user,
            "private_key_path": private_key_path
        }, opts)

config = pulumi.Config()
host = config.get("host") or "31.56.176.110"
user = config.get("user") or "root"
key_path = config.get("key_path") or "/Users/mac/.ssh/id_ed25519"

vps = VPSResource("vps-setup", host=host, user=user, private_key_path=key_path)

pulumi.export("vm_public_ip", host)
pulumi.export("ssh_connection", f"ssh {user}@{host}")
