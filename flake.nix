{
  description = "Led matrix flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    {
      self,
      nixpkgs,
      ...
    }:
    let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
      python = pkgs.python311Full;
    in
    {
      devShells.x86_64-linux.default = pkgs.mkShell {
        packages = [
          python
        ];
      };
    };
}
