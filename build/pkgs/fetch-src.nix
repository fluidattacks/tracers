{ repo
, commit
, digest
}:

let
  pkgs = import <nixpkgs> { };
in
  pkgs.fetchzip {
    url = "${repo}/archive/${commit}.zip";
    sha256 = digest;
  }
