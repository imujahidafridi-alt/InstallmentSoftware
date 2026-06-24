; Inno Setup Script for EasyQist Installer

[Setup]
AppName=EasyQist
AppVersion=1.2.0
AppPublisher=Afridi Labz
DefaultDirName={localappdata}\EasyQist
DefaultGroupName=EasyQist
OutputDir=dist
OutputBaseFilename=EasyQist_Setup
SetupIconFile=src\views\assets\app_icon.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\EasyQist.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion


[Icons]
Name: "{group}\EasyQist"; Filename: "{app}\EasyQist.exe"
Name: "{userdesktop}\EasyQist"; Filename: "{app}\EasyQist.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\EasyQist.exe"; Description: "{cm:LaunchProgram,EasyQist}"; Flags: nowait postinstall skipifsilent
