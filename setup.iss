[Setup]
AppName=Slate
AppVersion=1.1.0
AppPublisher=Sharjeel Ahmed
DefaultDirName={autopf}\Slate
DefaultGroupName=Slate
UninstallDisplayIcon={app}\slate.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=slate-setup
SetupIconFile=app\app_icon.ico
ChangesAssociations=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\slate\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Slate"; Filename: "{app}\slate.exe"
Name: "{autodesktop}\Slate"; Filename: "{app}\slate.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\slate.exe"; Description: "{cm:LaunchProgram,Slate}"; Flags: nowait postinstall skipifsilent

[Registry]
; Register .pdf file association for all users
Root: HKA; Subkey: "Software\Classes\.pdf\OpenWithProgids"; ValueType: string; ValueName: "Slate.PDF"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\Slate.PDF"; ValueType: string; ValueName: ""; ValueData: "PDF Document"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Slate.PDF\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\slate.exe,0"
Root: HKA; Subkey: "Software\Classes\Slate.PDF\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\slate.exe"" ""%1"""
