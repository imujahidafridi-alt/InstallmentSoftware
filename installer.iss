; Inno Setup Script for Asif Mobile Center Installer

[Setup]
AppName=Asif Mobile Center
AppVersion=1.2.0
AppPublisher=Asif Mobile Center
DefaultDirName={localappdata}\Asif Mobile Center
DefaultGroupName=Asif Mobile Center
OutputDir=dist
OutputBaseFilename=Asif_Mobile_Center_Setup
SetupIconFile=src\views\assets\app_icon.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\Asif Mobile Center.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion


[Icons]
Name: "{group}\Asif Mobile Center"; Filename: "{app}\Asif Mobile Center.exe"
Name: "{userdesktop}\Asif Mobile Center"; Filename: "{app}\Asif Mobile Center.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Asif Mobile Center.exe"; Description: "{cm:LaunchProgram,Asif Mobile Center}"; Flags: nowait postinstall skipifsilent
