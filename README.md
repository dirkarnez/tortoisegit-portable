https://github.com/activescott/lessmsi/releases/download/v1.10.0/lessmsi-v1.10.0.zip
https://download.tortoisegit.org/tgit/2.13.0.0/TortoiseGit-2.13.0.1-64bit.msi
.\lessmsi.exe x "C:\Users\19081126D\Downloads\TortoiseGit-2.13.0.1-64bit.msi" "Downloads\lessmsi-v1.10.0\target\"

@echo off
set DOWNLOADS_DIR=%USERPROFILE%\Downloads

SET PATH=^
%DOWNLOADS_DIR%;^
%DOWNLOADS_DIR%\PortableGit\bin;

start "" "SourceDir\Program Files\TortoiseGit\bin\TortoiseGitProc.exe" /command:commit /path:%1
pause
