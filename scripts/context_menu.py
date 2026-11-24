r"""Register (or remove) an Explorer context menu for portable TortoiseGit.

Single script, deterministic icons: every menu item points at a fixed icon
*resource ID* inside TortoiseGit.dll ("...\TortoiseGit.dll",-<ID>). Nothing is
extracted to disk and nothing depends on enumeration order.

The ID -> action mapping is taken from TortoiseGit's own sources:
  src/TortoiseShell/resource.h  (IDI_* values)
  src/TortoiseShell/MenuInfo.cpp (which IDI_* each shell command uses)
IDs are identical in 2.13.0.0 and 2.19.2.0. Before writing anything, the
script checks that every ID exists in the DLL and aborts otherwise.

Usage:
  python scripts\context_menu.py                       # install, TortoiseGit in C:\Apps\tortoisegit
  python scripts\context_menu.py --root D:\tools\tgit  # install, custom location
  python scripts\context_menu.py --dry-run             # print what would be written
  python scripts\context_menu.py --uninstall           # remove the menu
  python scripts\context_menu.py --export-reg out      # write out\context-menu-install.reg
                                                       # and out\context-menu-uninstall.reg

Writes only to HKEY_CURRENT_USER; no admin rights required.
"""

import argparse
import ctypes
import os
import sys
from ctypes import wintypes

DEFAULT_ROOT = r"C:\Apps\tortoisegit"

# Icon resource IDs in TortoiseGit.dll (names from src/TortoiseShell/resource.h).
IDI_PULL = 5
IDI_APP = 108
IDI_UPDATE = 122  # used by TortoiseGit for Fetch
IDI_COMMIT = 123
IDI_ADD = 124
IDI_REVERT = 125
IDI_RESOLVE = 127
IDI_SWITCH = 128
IDI_MERGE = 129
IDI_COPY = 132  # used by TortoiseGit for Create Branch
IDI_DELETE = 133
IDI_RENAME = 134
IDI_DIFF = 135
IDI_LOG = 136
IDI_SETTINGS = 138
IDI_CREATEREPOS = 139
IDI_RELOCATE = 141  # used by TortoiseGit for Sync
IDI_SHOWCHANGED = 143  # Check for modifications
IDI_BLAME = 5146
IDI_MENUFILE = 5154
IDI_MENUFOLDER = 5155
IDI_SHELVE = 5161  # Stash Save
IDI_PUSH = 5166
IDI_CLONE = 5167
IDI_REBASE = 5169

# (key, label, TortoiseGitProc /command, icon ID, separator before)
FOLDER_SUBMENU = [
    ("01_pull", "Pull...", "pull", IDI_PULL, False),
    ("02_fetch", "Fetch...", "fetch", IDI_UPDATE, False),
    ("03_push", "Push...", "push", IDI_PUSH, False),
    ("04_diff", "Diff", "diff", IDI_DIFF, True),
    ("05_log", "Show log", "log", IDI_LOG, True),
    ("06_status", "Check for modifications", "repostatus", IDI_SHOWCHANGED, False),
    ("07_rebase", "Rebase...", "rebase", IDI_REBASE, False),
    ("08_stash", "Stash Save", "stashsave", IDI_SHELVE, False),
    ("09_resolve", "Resolve...", "resolve", IDI_RESOLVE, True),
    ("10_revert", "Revert...", "revert", IDI_REVERT, False),
    ("11_switch", "Switch/Checkout...", "switch", IDI_SWITCH, True),
    ("12_merge", "Merge...", "merge", IDI_MERGE, False),
    ("13_branch", "Create Branch...", "branch", IDI_COPY, False),
    ("14_clone", "Git Clone...", "clone", IDI_CLONE, True),
    ("15_init", "Git Create Repository Here", "repocreate", IDI_CREATEREPOS, False),
    ("16_settings", "Settings", "settings", IDI_SETTINGS, True),
]

FILE_SUBMENU = [
    ("01_diff", "Diff", "diff", IDI_DIFF, False),
    ("02_prevdiff", "Diff with previous version", "prevdiff", IDI_DIFF, False),
    ("03_log", "Show log", "log", IDI_LOG, True),
    ("04_blame", "Blame", "blame", IDI_BLAME, False),
    ("05_status", "Check for modifications", "repostatus", IDI_SHOWCHANGED, False),
    ("06_resolve", "Resolve...", "resolve", IDI_RESOLVE, True),
    ("07_revert", "Revert...", "revert", IDI_REVERT, False),
    ("08_add", "Add...", "add", IDI_ADD, False),
    ("09_remove", "Delete", "remove", IDI_DELETE, False),
    ("10_rename", "Rename...", "rename", IDI_RENAME, False),
    ("11_settings", "Settings", "settings", IDI_SETTINGS, True),
]

# (registry base, %-token for the clicked path, submenu items, submenu icon)
TARGETS = [
    (r"Software\Classes\Directory\shell", "%1", FOLDER_SUBMENU, IDI_MENUFOLDER),
    (r"Software\Classes\Directory\Background\shell", "%V", FOLDER_SUBMENU, IDI_MENUFOLDER),
    (r"Software\Classes\*\shell", "%1", FILE_SUBMENU, IDI_MENUFILE),
]

TOP_LEVEL_KEYS = ["01_TGitSync", "02_TGitCommit", "03_TortoiseGitMenu"]
LEGACY_KEYS = ["TortoiseGitMenu"]  # left behind by earlier script versions

ECF_SEPARATORBEFORE = 0x20
ECF_SEPARATORAFTER = 0x40
RT_GROUP_ICON = 14
LOAD_LIBRARY_AS_DATAFILE = 0x2


def group_icon_ids(pe_path):
    """Return the set of numeric RT_GROUP_ICON resource IDs in a PE file."""
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.LoadLibraryExW.argtypes = [wintypes.LPCWSTR, wintypes.HANDLE, wintypes.DWORD]
    k32.LoadLibraryExW.restype = wintypes.HMODULE
    k32.FreeLibrary.argtypes = [wintypes.HMODULE]
    proc_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HMODULE, ctypes.c_void_p, ctypes.c_void_p, wintypes.LPARAM
    )
    k32.EnumResourceNamesW.argtypes = [wintypes.HMODULE, ctypes.c_void_p, proc_type, wintypes.LPARAM]

    hmod = k32.LoadLibraryExW(pe_path, None, LOAD_LIBRARY_AS_DATAFILE)
    if not hmod:
        raise OSError(ctypes.get_last_error(), f"cannot load {pe_path}")
    ids = set()

    def collect(_hmod, _type, name, _lparam):
        if name is not None and name >> 16 == 0:  # IS_INTRESOURCE
            ids.add(name)
        return True

    callback = proc_type(collect)  # keep a reference for the duration of the call
    try:
        k32.EnumResourceNamesW(hmod, RT_GROUP_ICON, callback, 0)
    finally:
        k32.FreeLibrary(hmod)
    return ids


def all_icon_ids():
    ids = {IDI_COMMIT, IDI_RELOCATE}
    for _, _, items, submenu_icon in TARGETS:
        ids.add(submenu_icon)
        ids.update(item[3] for item in items)
    return ids


class Registry:
    def __init__(self, dry_run):
        self.dry_run = dry_run
        if not dry_run:
            import winreg

            self.winreg = winreg

    def set(self, subkey, name, value):
        if self.dry_run:
            print(f"  HKCU\\{subkey}  {name or '(Default)'} = {value!r}")
            return
        wr = self.winreg
        kind = wr.REG_DWORD if isinstance(value, int) else wr.REG_SZ
        with wr.CreateKeyEx(wr.HKEY_CURRENT_USER, subkey, 0, wr.KEY_SET_VALUE) as key:
            wr.SetValueEx(key, name, 0, kind, value)

    def delete_tree(self, subkey):
        if self.dry_run:
            print(f"  delete HKCU\\{subkey}")
            return
        wr = self.winreg
        try:
            with wr.OpenKey(wr.HKEY_CURRENT_USER, subkey, 0, wr.KEY_READ) as key:
                children = []
                while True:
                    try:
                        children.append(wr.EnumKey(key, len(children)))
                    except OSError:
                        break
            for child in children:
                self.delete_tree(f"{subkey}\\{child}")
            wr.DeleteKey(wr.HKEY_CURRENT_USER, subkey)
        except FileNotFoundError:
            pass


class RegFile:
    """Same interface as Registry, but records the changes as a .reg file."""

    HKCU = "HKEY_CURRENT_USER"

    def __init__(self):
        self.lines = ["Windows Registry Editor Version 5.00", ""]
        self.current_key = None

    @staticmethod
    def quote(text):
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'

    def set(self, subkey, name, value):
        if subkey != self.current_key:
            if self.lines[-1] != "":
                self.lines.append("")
            self.lines.append(f"[{self.HKCU}\\{subkey}]")
            self.current_key = subkey
        data = f"dword:{value:08x}" if isinstance(value, int) else self.quote(value)
        self.lines.append(f"{'@' if name == '' else self.quote(name)}={data}")

    def delete_tree(self, subkey):
        self.lines.append(f"[-{self.HKCU}\\{subkey}]")
        self.current_key = None

    def save(self, path):
        # regedit's own export format: UTF-16 LE with BOM, CRLF line endings
        with open(path, "w", encoding="utf-16", newline="\r\n") as f:
            f.write("\n".join(self.lines) + "\n\n")


def remove_menu(reg, base):
    for name in TOP_LEVEL_KEYS + LEGACY_KEYS:
        reg.delete_tree(rf"{base}\{name}")


def install_menu(reg, base, token, items, submenu_icon, proc, icon):
    def command(name):
        return f'"{proc}" /command:{name} /path:"{token}"'

    remove_menu(reg, base)

    sync = rf"{base}\01_TGitSync"
    reg.set(sync, "MUIVerb", "Git Sync...")
    reg.set(sync, "Icon", icon(IDI_RELOCATE))
    reg.set(sync, "CommandFlags", ECF_SEPARATORBEFORE)
    reg.set(rf"{sync}\command", "", command("sync"))

    commit = rf"{base}\02_TGitCommit"
    reg.set(commit, "MUIVerb", "Git Commit...")
    reg.set(commit, "Icon", icon(IDI_COMMIT))
    reg.set(rf"{commit}\command", "", command("commit"))

    menu = rf"{base}\03_TortoiseGitMenu"
    reg.set(menu, "MUIVerb", "TortoiseGit")
    reg.set(menu, "Icon", icon(submenu_icon))
    reg.set(menu, "SubCommands", "")
    reg.set(menu, "CommandFlags", ECF_SEPARATORAFTER)
    for key, label, cmd, icon_id, sep_before in items:
        item = rf"{menu}\shell\{key}"
        reg.set(item, "MUIVerb", label)
        reg.set(item, "Icon", icon(icon_id))
        if sep_before:
            reg.set(item, "CommandFlags", ECF_SEPARATORBEFORE)
        reg.set(rf"{item}\command", "", command(cmd))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=DEFAULT_ROOT,
                        help=f"TortoiseGit folder containing bin\\ (default: {DEFAULT_ROOT})")
    parser.add_argument("--uninstall", action="store_true", help="remove the context menu")
    parser.add_argument("--dry-run", action="store_true", help="print registry changes only")
    parser.add_argument("--export-reg", metavar="DIR",
                        help="write install/uninstall .reg files to DIR instead of changing the registry")
    parser.add_argument("--reg-root", metavar="PATH",
                        help="with --export-reg: TortoiseGit path to write into the .reg files "
                             "(default: --root). The DLL is still checked under --root.")
    args = parser.parse_args()

    if os.name != "nt":
        sys.exit("Run this script on Windows.")
    if args.reg_root and not args.export_reg:
        parser.error("--reg-root requires --export-reg")

    if args.export_reg:
        export_reg_files(args)
        return

    reg = Registry(args.dry_run)

    if args.uninstall:
        for base, *_ in TARGETS:
            remove_menu(reg, base)
        print("[OK] TortoiseGit context menu removed.")
        return

    proc, icon = checked_paths(args.root)
    for base, token, items, submenu_icon in TARGETS:
        if args.dry_run:
            print(f"[{base}]")
        install_menu(reg, base, token, items, submenu_icon, proc, icon)
    print("[OK] TortoiseGit context menu installed for folders, folder background and files.")


def checked_paths(root, target_root=None):
    """Validate TortoiseGit under `root`; return (proc path, icon function) for `target_root`."""
    bin_dir = os.path.join(os.path.abspath(root), "bin")
    proc = os.path.join(bin_dir, "TortoiseGitProc.exe")
    dll = os.path.join(bin_dir, "TortoiseGit.dll")
    for path in (proc, dll):
        if not os.path.isfile(path):
            sys.exit(f"[ERROR] Not found: {path}  (use --root)")

    missing = sorted(all_icon_ids() - group_icon_ids(dll))
    if missing:
        sys.exit(f"[ERROR] {dll} has no icon resource(s) {missing}; "
                 "this TortoiseGit version uses different IDs. Nothing was changed.")

    if target_root:
        target_bin = os.path.join(target_root, "bin")
        proc = os.path.join(target_bin, "TortoiseGitProc.exe")
        dll = os.path.join(target_bin, "TortoiseGit.dll")

    def icon(resource_id):
        return f'"{dll}",-{resource_id}'  # negative = resource ID, not index

    return proc, icon


def export_reg_files(args):
    target_root = args.reg_root or os.path.abspath(args.root)
    proc, icon = checked_paths(args.root, target_root)

    install, uninstall = RegFile(), RegFile()
    for base, token, items, submenu_icon in TARGETS:
        install_menu(install, base, token, items, submenu_icon, proc, icon)
        remove_menu(uninstall, base)

    os.makedirs(args.export_reg, exist_ok=True)
    for name, reg in (("context-menu-install.reg", install), ("context-menu-uninstall.reg", uninstall)):
        path = os.path.join(args.export_reg, name)
        reg.save(path)
        print(f"[OK] Wrote {path}")
    print(f"     TortoiseGit path inside the .reg files: {target_root}")


if __name__ == "__main__":
    main()
