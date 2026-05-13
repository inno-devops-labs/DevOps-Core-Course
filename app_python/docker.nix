
{ pkgs ? import <nixpkgs> {} }:

let

  app = import ./default.nix { inherit pkgs; };

in

pkgs.dockerTools.buildLayeredImage {

  name = "devops-info-service-nix";

  tag = "1.0.0";

  contents = [ app pkgs.coreutils pkgs.bash pkgs.python3 ];

  config = {

    Entrypoint = [ "${pkgs.bash}/bin/bash" "-c" ];

    Cmd = [ "${app}/bin/devops-info-service" ];

    Env = [ "PORT=5000" "HOST=0.0.0.0" ];

    ExposedPorts = { "5000/tcp" = {}; };

  };

  created = "1970-01-01T00:00:01Z";

}

