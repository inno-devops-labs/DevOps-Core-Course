{
  description = "DevOps Info Service - Reproducible Build with Nix Flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      # Mac M-series (arm64)
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
          python313
          python313Packages.flask
          python313Packages.prometheus-client
        ];
        shellHook = ''
          echo "DevOps Info Service dev environment"
          echo "Python: $(python3 --version)"
          echo "Flask: $(python3 -c 'import flask; print(flask.__version__)')"
        '';
      };
    };
}
