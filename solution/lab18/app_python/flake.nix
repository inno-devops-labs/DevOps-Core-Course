{
  description = "DevOps Info Service reproducible Nix build for Lab 18";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python313
          python313Packages.fastapi
          python313Packages.prometheus-client
          python313Packages.uvicorn
        ];

        shellHook = ''
          echo "Lab 18 Nix shell: $(python --version)"
        '';
      };
    };
}
