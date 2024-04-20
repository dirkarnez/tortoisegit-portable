tortoisegit-portable
====================
### How to use
- [Appendix D. Automating TortoiseGit – TortoiseGit – Documentation – TortoiseGit – Windows Shell Interface to Git](https://tortoisegit.org/docs/tortoisegit/tgit-automation.html)
  - commit
    ```cmd
    @echo off
    set DOWNLOADS_DIR=%USERPROFILE%\Downloads

    SET PATH=^
    %DOWNLOADS_DIR%;^
    %DOWNLOADS_DIR%\PortableGit\bin;
    
    start "" "%~dp0TortoiseGitProc.exe" /command:commit /path:%1
    pause
    ```
  - `/command:settings`
