{
  pkgs ? import (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/50ab793786d9de88ee30ec4e4c24fb4236fc2674.tar.gz";
    sha256 = "1s2gr5rcyqvpr58vxdcb095mdhblij9bfzaximrva2243aal3dgx";
  })
    { },
}:

let
  app = import ./default.nix { inherit pkgs; };
in

pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app pkgs.cacert ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "8000/tcp" = { };
    };
    Env = [
      "HOST=0.0.0.0"
      "PORT=8000"
      "PYTHONUNBUFFERED=1"
    ];
  };

  # OCI "created" field fixed to Unix epoch + 1s so the manifest does not embed wall-clock time (helps bit-reproducible tarballs).
  created = "1970-01-01T00:00:01Z";
}
