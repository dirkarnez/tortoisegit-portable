tortoisegit-portable
====================
### How to use
- [Appendix D. Automating TortoiseGit – TortoiseGit – Documentation – TortoiseGit – Windows Shell Interface to Git](https://tortoisegit.org/docs/tortoisegit/tgit-automation.html)
  - `/command:settings`

### Explorer context menu
The portable build has no installer, so the TortoiseGit shell extension is not registered and
Explorer shows no TortoiseGit menu. [`scripts/context_menu.py`](scripts/context_menu.py) adds a
lightweight replacement that calls `TortoiseGitProc.exe` directly:

- **Git Sync...** and **Git Commit...** at the top level
- a **TortoiseGit** submenu with Pull, Fetch, Push, Diff, Show log, Check for modifications,
  Rebase, Stash Save, Resolve, Revert, Switch/Checkout, Merge, Create Branch, Clone,
  Create Repository and Settings (folders), or Diff, Diff with previous version, Show log,
  Blame, Check for modifications, Resolve, Revert, Add, Delete, Rename and Settings (files)

It is registered for folders, the folder background and files. It writes only to
`HKEY_CURRENT_USER`, so no administrator rights are needed. On Windows 11 the entries appear
under **Show more options** (or <kbd>Shift</kbd>+right-click).

#### Requirements
- Windows 10/11
- Python 3.8 or newer (not needed for the `.reg` files described below). The script uses only the standard library, so there is nothing to
  `pip install` and no `requirements.txt`.
- An unpacked portable TortoiseGit (from the release zip). The script expects the folder that
  contains `bin\TortoiseGitProc.exe` and `bin\TortoiseGit.dll`; the default is
  `C:\Apps\tortoisegit`.

#### Usage
Run from the repository root:

```powershell
# install the menu (TortoiseGit unpacked to C:\Apps\tortoisegit)
python scripts\context_menu.py

# TortoiseGit unpacked somewhere else
python scripts\context_menu.py --root D:\tools\tortoisegit

# preview the registry changes without writing anything
python scripts\context_menu.py --dry-run

# remove the menu again
python scripts\context_menu.py --uninstall
```

Re-running the install is safe: it removes the previous entries before writing new ones. If you
move the TortoiseGit folder, run the script again with the new `--root`.

#### Without Python: `.reg` files in the release zip
Each release zip contains two ready-made registry files next to `bin\`. They make exactly the
same registry changes as the Python script:

| File | What it does |
|---|---|
| `context-menu-install.reg` | adds the context menu (removes older entries first) |
| `context-menu-uninstall.reg` | removes the context menu |

Double-click a file and confirm, or run it from a terminal:

```powershell
reg import C:\Apps\tortoisegit\context-menu-install.reg
```

> [!WARNING]
> **The bundled `context-menu-install.reg` only works if TortoiseGit is unpacked to
> `C:\Apps\tortoisegit`.** A `.reg` file can't use relative paths, so this location is written into
> every icon and command entry. If you unpack the zip anywhere else, the menu entries still
> appear, but the icons are blank and clicking an item fails with a "Windows cannot find …"
> error, because `TortoiseGitProc.exe` isn't where the entries point.
>
> For any other location, either use the Python script with `--root`, or generate `.reg` files
> for your own path:
>
> ```powershell
> python scripts\context_menu.py --root D:\tools\tortoisegit --export-reg D:\tools\tortoisegit
> ```
>
> `context-menu-uninstall.reg` doesn't contain any paths and works for every location.

`--export-reg DIR` writes both files to `DIR` without touching the registry. It checks the icon
IDs in the DLL under `--root` first. To check one copy of TortoiseGit but write a different path
into the files (this is how the release build does it), add `--reg-root`:

```powershell
python scripts\context_menu.py --root .\extracted\TortoiseGit --reg-root C:\Apps\tortoisegit --export-reg out
```

#### Icons
Each menu item uses an icon from `TortoiseGit.dll` by its fixed resource ID
(`"...\TortoiseGit.dll",-<ID>`), which is the same mapping TortoiseGit's own shell extension uses
(`src/TortoiseShell/resource.h` and `MenuInfo.cpp`). The icons therefore always match their
commands, and nothing is extracted to disk. Before writing to the registry, the script checks
that every icon ID exists in the DLL. If a future TortoiseGit version changes the IDs, it stops
with an error and changes nothing.
