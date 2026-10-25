; Aegis White installer — Ohana Tech Solutions
; Build with Inno Setup 6 after PyInstaller creates dist\AegisWhite.exe.
#define AppName "Aegis White"
#define AppVersion "0.1.0"
#define AppPublisher "Ohana Tech Solutions"
[Setup]
AppId={{9FD1B87A-7518-4683-AD82-0F0D6DF3D4A5}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Aegis White
DefaultGroupName=Aegis White
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=output
OutputBaseFilename=AegisWhite_Setup_v{#AppVersion}_x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\AegisWhite.exe

[Files]
Source: "..\dist\AegisWhite.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Aegis White"; Filename: "{app}\AegisWhite.exe"
Name: "{autodesktop}\Aegis White"; Filename: "{app}\AegisWhite.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\AegisWhite.exe"; Description: "Launch Aegis White"; Flags: nowait postinstall skipifsilent
