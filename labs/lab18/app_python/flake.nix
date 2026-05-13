{
  description = "DevOps Info Service - Reproducible build with Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = pkgs.callPackage ./default.nix {};
        dockerImage = pkgs.callPackage ./docker.nix {};
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python313
          python313Packages.fastapi
          python313Packages.uvicorn
          python313Packages.prometheus-client
          python313Packages.python-json-logger
        ];

        shellHook = ''
          echo "DevOps Info Service — Nix development shell"
          echo "Python: $(python --version)"
          echo "Run: python app.py"
        '';
      };
    };
}
