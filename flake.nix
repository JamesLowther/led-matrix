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
      python = pkgs.python312;
    in
    {
      devShells.x86_64-linux.default = pkgs.mkShell {
        packages = [
          python
          python.pkgs.pyside6
          python.pkgs.requests
          python.pkgs.numpy
          python.pkgs.pillow
          python.pkgs.python-dotenv
        ];
      };
    };
}

# {
#   pkgs ? import <nixpkgs> { },
# }:
# pkgs.mkShell {
#   buildInputs = with pkgs; [
#     python3
#     python3.pkgs.pyside6
#     python3.pkgs.requests
#     python3.pkgs.pillow
#     python3.pkgs.numpy
#   ];
# }
