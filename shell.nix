{
  pkgs ? import <nixpkgs> { },
}:

pkgs.mkShell {
  buildInputs = [
    pkgs.python313
    pkgs.python313Packages.pygobject3
    pkgs.gobject-introspection
    pkgs.webkitgtk_4_1 # for GTK backend
    pkgs.gtk3
  ];
}
