{ pkgs ? import <nixpkgs> {} }:

pkgs.buildGoModule {
  pname = "devops-info-service-go";
  version = "1.0.0";
  src = ./.;

  vendorHash = null;
}
