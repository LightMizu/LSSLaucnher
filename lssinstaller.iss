#define MyAppName "LSSLaucher"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "LSSProduction"
#define MyAppURL "https://t.me"
#define MyAppExeName "lsslauncher.exe"

[Setup]
AppId={{0166C96B-B205-47A4-8461-D5D2E9EFD71B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableDirPage=no
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputBaseFilename=mysetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; Кастомизация
SetupIconFile=installer_assets\setup.ico
WizardImageFile=installer_assets\sidebar.bmp
WizardSmallImageFile=installer_assets\banner.png

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "build\windows\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
; ярлык без аргументов
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; иконка на рабочий стол (с аргументами)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; запуск сразу после установки с аргументами
Filename: "{app}\{#MyAppExeName}"; \
  Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
  Flags: nowait postinstall skipifsilent
