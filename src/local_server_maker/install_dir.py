import os
from pathlib import Path

from local_server_maker.links import is_reparse_point


def require_removable_install_dir(
    path: Path, project_root: Path, steamcmd_dir: Path
) -> None:
    resolved = path.resolve()
    anchor = Path(resolved.anchor)
    if resolved == anchor or resolved.parent == anchor:
        raise ValueError(f"refusing to remove {resolved}")
    if overlaps(resolved, project_root.resolve()):
        raise ValueError(f"refusing to remove {resolved} because it overlaps the project")
    if overlaps(resolved, steamcmd_dir.resolve()):
        raise ValueError(f"refusing to remove {resolved} because it overlaps SteamCMD")


def require_removable_steamcmd_dir(path: Path, project_root: Path) -> None:
    resolved = path.resolve()
    root = project_root.resolve()
    anchor = Path(resolved.anchor)
    if resolved == anchor or resolved.parent == anchor:
        raise ValueError(f"refusing to remove {resolved}")
    if resolved == root or contains(resolved, root):
        raise ValueError(f"refusing to remove {resolved} because it contains the project")


def remove_tree(path: Path) -> None:
    if is_reparse_point(path):
        os.rmdir(path)
        return
    if path.is_dir():
        for child in list(path.iterdir()):
            remove_tree(child)
        os.rmdir(path)
        return
    path.unlink()


def contains(parent: Path, child: Path) -> bool:
    parent_text = os.path.normcase(str(parent))
    child_text = os.path.normcase(str(child))
    return child_text.startswith(with_sep(parent_text))


def overlaps(left: Path, right: Path) -> bool:
    left_text = os.path.normcase(str(left))
    right_text = os.path.normcase(str(right))
    if left_text == right_text:
        return True
    return left_text.startswith(with_sep(right_text)) or right_text.startswith(
        with_sep(left_text)
    )


def with_sep(path: str) -> str:
    if path.endswith("\\") or path.endswith("/"):
        return path
    return path + os.sep
