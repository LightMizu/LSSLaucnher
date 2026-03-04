{
  pkgs ? import <nixpkgs> { },
}:

let
  lib = pkgs.lib;

  python = pkgs.python313.withPackages (
    ps: with ps; [
      pyqt6
      pywebview
      # если ты реально используешь poetry внутри этого же python,
      # можно оставить так; иначе лучше pkgs.poetry отдельно (ниже)
    ]
  );

  nixLdLibs = [
    # Qt
    pkgs.qt6.qtbase
    pkgs.qt6.qtwayland
    pkgs.qt6.qtwebengine
    pkgs.qt6.qtwebchannel
    pkgs.qt6.qtdeclarative

    # OpenGL / GPU
    pkgs.libglvnd
    pkgs.mesa
    pkgs.stdenv.cc.cc.lib
    pkgs.libgbm
    pkgs.krb5

    # X11
    pkgs.xorg.libX11
    pkgs.xorg.libXext
    pkgs.xorg.libXi
    pkgs.xorg.libXtst
    pkgs.xorg.libXrandr
    pkgs.xorg.libXrender
    pkgs.xorg.libXcomposite
    pkgs.xorg.libXdamage
    pkgs.xorg.libXfixes
    pkgs.xorg.libxcb
    pkgs.xorg.libxkbfile
    pkgs.xorg.libxshmfence

    # Input
    pkgs.libxkbcommon

    # System
    pkgs.dbus
    pkgs.systemd
    pkgs.glib

    # Fonts / text
    pkgs.fontconfig
    pkgs.freetype
    pkgs.expat

    # Audio
    pkgs.alsa-lib

    # Compression
    pkgs.zlib
    pkgs.zstd
    pkgs.brotli

    # Crypto (QtWebEngine)
    pkgs.nss
    pkgs.nspr

    pkgs.vulkan-loader
    pkgs.vulkan-validation-layers
  ];
in
pkgs.mkShell {
  name = "pyqt-shell";

  # Главное: один python окружением — тогда биндинги точно видны
  packages = [
    python
    pkgs.poetry

    pkgs.qt6.qtbase
    pkgs.qt6.qtwayland
    pkgs.qt6.qtwebengine
    pkgs.qt6.qtwebchannel
    pkgs.qt6.qtdeclarative

    pkgs.xdg-desktop-portal
  ];

  NIX_LD = lib.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";
  NIX_LD_LIBRARY_PATH = lib.makeLibraryPath nixLdLibs;

  shellHook = ''
    export PYWEBVIEW_GUI=qt
    export QT_QPA_PLATFORM=xcb
    export LD_LIBRARY_PATH="$NIX_LD_LIBRARY_PATH:$LD_LIBRARY_PATH"

    # Qt plugins (platforms/xcb и т.п.)
    export QT_PLUGIN_PATH="${pkgs.qt6.qtbase}/${pkgs.qt6.qtbase.qtPluginPrefix}:$QT_PLUGIN_PATH"

    # QML (без qtQmlPrefix, совместимо с разными nixpkgs)
    if [ -d "${pkgs.qt6.qtdeclarative}/lib/qt-6/qml" ]; then
      export QML2_IMPORT_PATH="${pkgs.qt6.qtdeclarative}/lib/qt-6/qml:$QML2_IMPORT_PATH"
    fi
    if [ -d "${pkgs.qt6.qtdeclarative}/lib/qt6/qml" ]; then
      export QML2_IMPORT_PATH="${pkgs.qt6.qtdeclarative}/lib/qt6/qml:$QML2_IMPORT_PATH"
    fi

    export QT_QPA_PLATFORMTHEME=qt6ct
    export QTWEBENGINE_CHROMIUM_FLAGS="--disable-vulkan"

    python -c "import PyQt6; import PyQt6.QtCore; print('PyQt6 OK:', PyQt6.__file__)"
  '';
}
