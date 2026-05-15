{
  description = "DevOps Info Service reproducible build with Nix Flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system}.default = import ./default.nix { inherit pkgs; };
      packages.${system}.dockerImage = import ./docker.nix { inherit pkgs; };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          pkgs.python3
          pkgs.python3Packages.fastapi
          pkgs.python3Packages.uvicorn
        ];
      };
    };
}
