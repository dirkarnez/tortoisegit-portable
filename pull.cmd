@echo off
set DOWNLOADS_DIR=%USERPROFILE%\Downloads

SET PATH=^
%DOWNLOADS_DIR%;^
%DOWNLOADS_DIR%\PortableGit\bin;


start "" "%DOWNLOADS_DIR%\tortoisegit-portable-v2.13.0.1\bin\TortoiseGitProc.exe" /command:pull /path:"%~1"
pause
