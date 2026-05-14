{ pkgs ? import <nixpkgs> {} }:

let
  # Bundle exact Python interpreter with pinned packages from nixpkgs.
  # python3.withPackages produces a single derivation whose closure contains
  # Python + every listed package with all transitive deps resolved at
  # evaluation time — not at runtime like pip does.
  python = pkgs.python3.withPackages (ps: with ps; [
    flask
    prometheus-client
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";

  # src = ./. tells Nix to hash the current directory and use it as
  # the build input.  Any change to any file changes the hash →
  # forces a rebuild; identical files → reuses cached store path.
  src = ./.;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/lib/devops-info-service

    cp app.py $out/lib/devops-info-service/app.py

    # makeWrapper generates a shell wrapper that sets up the runtime
    # environment before exec-ing the real interpreter.  VISITS_FILE
    # is redirected to /tmp so the read-only Nix store is not written.
    makeWrapper ${python}/bin/python3 $out/bin/devops-info-service \
      --add-flags "$out/lib/devops-info-service/app.py" \
      --set VISITS_FILE "/tmp/devops-info-visits"
  '';

  meta = {
    description = "DevOps Info Service — Lab 1 app rebuilt with Nix";
    mainProgram = "devops-info-service";
  };
}
