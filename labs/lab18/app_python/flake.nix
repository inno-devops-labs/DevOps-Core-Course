{
  description = "DevOps Info Service — reproducible build with Nix Flakes (Lab 18)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      # macOS ARM (M1/M2/M3). For other systems change accordingly:
      #   Linux x86_64:  "x86_64-linux"
      #   Linux ARM:     "aarch64-linux"
      #   Mac Intel:     "x86_64-darwin"
      #   Mac M1/M2/M3:  "aarch64-darwin"
      system = "aarch64-darwin";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python312
          python312Packages.fastapi
          python312Packages.uvicorn
          python312Packages.prometheus-client
        ];

        shellHook = ''
          echo "Lab 18 dev shell — Python $(python3 --version), all deps pinned via flake.lock"
        '';
      };
    };
}
