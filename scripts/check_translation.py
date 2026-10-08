"""Check the translations of the ReefTank integration.

- every `translation_key` used by an entity has a name in strings.json and
  in every translations/*.json;
- every translation file has exactly the keys of strings.json (nothing
  missing, nothing left over).
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

from colorama import Fore, Style

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "custom_components" / "reeftank"
PLATFORMS = ("sensor", "event")


def flatten(data: object, prefix: str = "") -> set[str]:
    """Dotted paths of every leaf of a JSON object."""
    if not isinstance(data, dict):
        return {prefix}
    keys: set[str] = set()
    for key, value in data.items():
        keys |= flatten(value, f"{prefix}.{key}" if prefix else key)
    return keys


def keys_in_code() -> set[str]:
    """`<platform>.<translation key>` of every entity, read from the code."""
    consts = {}
    tree = ast.parse((BASE / "const.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign | ast.Assign):
            target = node.target if isinstance(node, ast.AnnAssign) else node.targets[0]
            if (
                isinstance(target, ast.Name)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                consts[target.id] = node.value.value
    found: set[str] = set()
    for platform in PLATFORMS:
        tree = ast.parse((BASE / f"{platform}.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            # super().__init__(data, aquarium_id, KEY_X)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "__init__"
                and len(node.args) == 3
                and isinstance(node.args[2], ast.Name)
                and node.args[2].id in consts
            ):
                found.add(f"{platform}.{consts[node.args[2].id]}")
    return found


def main() -> int:
    """Return 0 when everything matches."""
    ok = True
    strings = json.loads((BASE / "strings.json").read_text(encoding="utf-8"))
    reference = flatten(strings)
    for key in sorted(keys_in_code()):
        if f"entity.{key}.name" not in reference:
            ok = False
            print(f"{Fore.RED}strings.json: missing entity.{key}.name{Style.RESET_ALL}")
    for file in sorted((BASE / "translations").glob("*.json")):
        keys = flatten(json.loads(file.read_text(encoding="utf-8")))
        for missing in sorted(reference - keys):
            ok = False
            print(f"{Fore.RED}{file.name}: missing {missing}{Style.RESET_ALL}")
        for extra in sorted(keys - reference):
            ok = False
            print(
                f"{Fore.YELLOW}{file.name}: not in strings.json {extra}{Style.RESET_ALL}"
            )
    if ok:
        print(f"{Fore.GREEN}Translations OK{Style.RESET_ALL}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
