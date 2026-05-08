{
  description = "DevOps Info Service reproducible builds";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
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

      defaultPackage.${system} = self.packages.${system}.default;

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [ python3 python3Packages.fastapi python3Packages.uvicorn ];
      };
    };
}
