{
  pkgs ? import <nixpkgs> { },
}:

let
  gstPackages = with pkgs.gst_all_1; [
    gstreamer
    gst-plugins-base
    gst-plugins-good
    gst-plugins-bad
    gst-libav
  ];

  gsettingsPackages = [
    pkgs.gsettings-desktop-schemas
    pkgs.gtk3
  ];
in

pkgs.mkShell {
  buildInputs = [
    pkgs.python313
    pkgs.uv
    pkgs.python313Packages.pygobject3
    pkgs.gobject-introspection

    # GTK / WebKit backend
    pkgs.webkitgtk_4_1
    pkgs.gtk3

    # GLib / GIO / TLS
    pkgs.glib
    pkgs.glib-networking
    pkgs.gsettings-desktop-schemas
    pkgs.dconf

    # Certificates
    pkgs.cacert

    # Useful GTK runtime assets
    pkgs.adwaita-icon-theme
    pkgs.hicolor-icon-theme
    pkgs.shared-mime-info
  ]
  ++ gstPackages;

  shellHook = ''
    # GStreamer plugins: fixes "GStreamer element appsink not found"
    export GST_PLUGIN_SYSTEM_PATH_1_0="${pkgs.lib.makeSearchPath "lib/gstreamer-1.0" gstPackages}:$GST_PLUGIN_SYSTEM_PATH_1_0"
    export GST_PLUGIN_PATH_1_0="$GST_PLUGIN_SYSTEM_PATH_1_0"

    # GSettings schemas: fixes "No GSettings schemas are installed on the system"
    export XDG_DATA_DIRS="${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}:${pkgs.gtk3}/share/gsettings-schemas/${pkgs.gtk3.name}:${pkgs.shared-mime-info}/share:$XDG_DATA_DIRS"

    # GIO TLS modules
    export GIO_EXTRA_MODULES="${pkgs.glib-networking}/lib/gio/modules"
    export GIO_USE_TLS=gnutls
    export GDK_BACKEND=x11
    export WEBKIT_DISABLE_DMABUF_RENDERER=1
    # Certificates
    export SSL_CERT_FILE="${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
    export G_TLS_CA_FILE="$SSL_CERT_FILE"

    echo "Dev shell ready"
    echo "Check GStreamer with: gst-inspect-1.0 appsink"
  '';
}
