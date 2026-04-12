{
  description = "DevOps Info Service";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        app = pkgs.callPackage ./default.nix {};
        
      in {
        packages.default = app;
        apps.default = flake-utils.lib.mkApp {
          drv = app;
          name = "devops-info-service";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = [ pkgs.python3 pkgs.python3Packages.flask ];
        };
      }
    );
}
