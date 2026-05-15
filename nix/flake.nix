{
  description = "DevOps Core reproducible builds";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs =
    { self, nixpkgs }:
    let
      lib = nixpkgs.lib;
      systems = [ "x86_64-linux" ];
      forAllSystems = lib.genAttrs systems;
      pkgsFor = system: import nixpkgs { inherit system; };
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = pkgsFor system;
          appPackage = pkgs.callPackage ./package.nix {
            appSrc = ../app_python;
          };
        in
        {
          default = appPackage;
          devops-info-service = appPackage;
          dockerImage = pkgs.callPackage ./docker.nix {
            inherit appPackage;
          };
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/devops-info-service";
        };
      });

      checks = forAllSystems (system: {
        default = self.packages.${system}.default;
      });

      devShells = forAllSystems (system: {
        default = (pkgsFor system).callPackage ./devshell.nix { };
      });

      formatter = forAllSystems (
        system:
        let
          pkgs = pkgsFor system;
        in
        pkgs.writeShellApplication {
          name = "format-nix";
          runtimeInputs = [ pkgs.nixfmt-rfc-style ];
          text = ''
            if [ "$#" -eq 0 ]; then
              if [ -f flake.nix ] && [ -f package.nix ]; then
                set -- flake.nix *.nix
              else
                set -- nix/flake.nix nix/*.nix
              fi
            fi
            exec nixfmt "$@"
          '';
        }
      );
    };
}
