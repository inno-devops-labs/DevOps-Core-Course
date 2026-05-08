{ pkgs ? import <nixpkgs> { } }:

pkgs.buildGoModule {
  pname = "devops-info-service-go";
  version = "1.0.0";
  src = ../app_go;

  vendorHash = null;

  postInstall = ''
    mv $out/bin/devops-info-service $out/bin/devops-info-service-go
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service (Go) rebuilt with Nix for reproducibility";
    license = licenses.mit;
    platforms = platforms.unix;
    mainProgram = "devops-info-service-go";
  };
}
