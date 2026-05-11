{
  description = "DevOps Info Service — reproducible build (Lab 18)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs =
    { self, nixpkgs }:
    let
      # Lab VM uses Linux x86_64. On macOS (aarch64-darwin / x86_64-darwin) set system to your platform or use a Linux remote builder for dockerTools.
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system}.default = import ./default.nix { inherit pkgs; };
      packages.${system}.dockerImage = import ./docker.nix { inherit pkgs; };

      devShells.${system}.default = pkgs.mkShell {
        name = "devops-info-service-dev";
        buildInputs = with pkgs; [
          python3
          python3Packages.fastapi
          python3Packages.uvicorn
          python3Packages.prometheus-client
        ];
        shellHook = ''
          echo "devops-info-service devshell (Python + FastAPI deps from flake inputs)"
        '';
      };
    };
}
