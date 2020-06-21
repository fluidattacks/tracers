{ repo
, commit
, digest
}:

let
  src = import ./fetch-src.nix {
    inherit repo commit digest;
  };
in
  import src { }
