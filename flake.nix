{
  description = "WebView application environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          pkg-config
          gobject-introspection
          fontconfig

        ];

        buildInputs = with pkgs; [

          gtk3
          webkitgtk_4_1
          glib
          gdk-pixbuf
          cairo
          pango
          atk
        ];
      };
    };
}
