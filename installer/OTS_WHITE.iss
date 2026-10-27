; OTS W.H.I.T.E. (White Hat Infiltration Testing Engine) installer — Ohana Tech Solutions
; Build with Inno Setup 6 after PyInstaller creates dist\OTS_WHITE.exe.
#define AppName "OTS W.H.I.T.E."
#define AppVersion "0.1.0"
#define AppPublisher "Ohana Tech Solutions"
[Setup]
AppId={{9FD1B87A-7518-4683-AD82-0F0D6DF3D4A5}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\OTS W.H.I.T.E.
DefaultGroupName=OTS W.H.I.T.E.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=output
OutputBaseFilename=OTS_WHITE_Setup_v{#AppVersion}_x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\OTS_WHITE.exe

[Files]
Source: "..\dist\OTS_WHITE.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\OTS W.H.I.T.E."; Filename: "{app}\OTS_WHITE.exe"
Name: "{autodesktop}\OTS W.H.I.T.E."; Filename: "{app}\OTS_WHITE.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\OTS_WHITE.exe"; Description: "Launch OTS W.H.I.T.E."; Flags: nowait postinstall skipifsilent
