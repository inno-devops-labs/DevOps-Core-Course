{ pkgs ? import <nixpkgs> {} }:

let
  linuxSystem =
    if pkgs.stdenv.isDarwin then
      (if pkgs.stdenv.hostPlatform.isAarch64 then "aarch64-linux" else "x86_64-linux")
    else
      pkgs.system;
  linuxPkgs = import <nixpkgs> { system = linuxSystem; };
  app = import ./default.nix { pkgs = linuxPkgs; };
in
linuxPkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "8080/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
}
