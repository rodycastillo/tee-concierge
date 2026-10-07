"""`tee-menu validate [file...]`: check menu files before they can reach a customer.

Runs the schema, structural rules and a dry-run render of every reachable screen.
Exits non-zero on the first file with problems, so it can gate CI.
"""

import argparse
import asyncio
import sys

from tee_concierge.application.menu.builder import MenuConfigError
from tee_concierge.application.menu.dryrun import dry_run
from tee_concierge.config import get_settings
from tee_concierge.infrastructure.menu.loader import load_menu


def _validate(path: str) -> list[str]:
    try:
        menu = load_menu(path)
    except MenuConfigError as error:
        return error.errors
    return asyncio.run(dry_run(menu))


def main() -> None:
    parser = argparse.ArgumentParser(prog="tee-menu", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate menu files")
    validate.add_argument("files", nargs="*", help="defaults to $MENU_CONFIG")
    args = parser.parse_args()

    failed = False
    for path in args.files or [get_settings().menu_config]:
        problems = _validate(path)
        if problems:
            failed = True
            print(f"FAIL {path}")
            print("\n".join(f"  - {p}" for p in problems))
        else:
            print(f"ok   {path}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
