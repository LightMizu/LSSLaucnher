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
    pkgs.glib-networking
    pkgs.cacert
  ];
  shellHook = ''
    export GIO_EXTRA_MODULES="${pkgs.glib-networking}/lib/gio/modules"
    export GIO_USE_TLS=gnutls
    export SSL_CERT_FILE="${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
    export G_TLS_CA_FILE="$SSL_CERT_FILE"
  '';
}
