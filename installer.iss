#define MyAppName "PyDex"
#define MyAppJP "パイデックス"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "the l house"
#define MyAppExeName "PyDex.exe"

[Setup]
AppId={{8F3A2B1C-7D4E-4A5F-9C1B-PYDEX000001}}
AppName={#MyAppName} {#MyAppJP}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=PyDex-Setup-{#MyAppVersion}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{app}\output"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify

[Files]
Source: "dist\PyDex\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\PyDex\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} {#MyAppJP}"; Flags: nowait postinstall skipifsilent
