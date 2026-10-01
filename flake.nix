{
  description = "LSS Launcher with the Qt WebEngine backend";

  inputs.nixpkgs.url = "github:nixos/nixpkgs";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      pythonPackages = pkgs.python313Packages;

      playsound3 = pythonPackages.buildPythonPackage {
        pname = "playsound3";
        version = "3.3.1";
        pyproject = true;
        src = pkgs.fetchPypi {
          pname = "playsound3";
          version = "3.3.1";
          sha256 = "3f0eb87d5ff2061d07663c4b010b8e7d66c274344712b01d561a0a73447ef41d";
        };
        build-system = [ pythonPackages.hatchling ];
        pythonImportsCheck = [ "playsound3" ];
      };

      # Keep pywebview on the PyQt6 bindings used by this project.
      pywebview = pythonPackages.pywebview.overridePythonAttrs (old: {
        dependencies = builtins.filter
          (dependency: dependency != pythonPackages.pyside6)
          old.dependencies;
      });
      python = pkgs.python313.withPackages (ps: [
        ps.requests
        ps.psutil
        ps.aiohttp
        ps.loguru
        ps.qtpy
        ps.pyqt6
        ps.pyqt6-webengine
        pywebview
        playsound3
      ]);

      launcher = pkgs.stdenvNoCC.mkDerivation {
        pname = "lss-launcher";
        version = "0.1.0";
        src = self;
        nativeBuildInputs = [ pkgs.makeWrapper pkgs.qt6.wrapQtAppsHook ];
        buildInputs = [ pkgs.qt6.qtbase pkgs.qt6.qtwebengine pkgs.qt6.qtwayland ];
        dontWrapQtApps = true;
        dontConfigure = true;
        dontBuild = true;
        installPhase = ''
          runHook preInstall
          mkdir -p "$out/share/lss-launcher" "$out/bin"
          cp -r src ui "$out/share/lss-launcher/"
          makeWrapper ${python}/bin/python "$out/bin/lss-launcher" \
            "''${qtWrapperArgs[@]}" \
            --set QT_API pyqt6 \
            --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.mpv ]} \
            --add-flags "$out/share/lss-launcher/src/main.py"
          runHook postInstall
        '';
      };
    in {
      packages.${system}.default = launcher;
      apps.${system}.default = {
        type = "app";
        program = "${launcher}/bin/lss-launcher";
      };

      devShells.${system}.default = pkgs.mkShell {
        inputsFrom = [ launcher ];
        packages = [ python pkgs.mpv ];
        shellHook = ''
          export QT_API=pyqt6
          export QT_PLUGIN_PATH="${pkgs.qt6.qtbase}/lib/qt-6/plugins:${pkgs.qt6.qtwayland}/lib/qt-6/plugins''${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"
        '';
      };
    };
}
