"""Check one observation file against the contract, without changing it.

usage: python -m playend.contract.validate observation.json [--require-v2]

Without --require-v2, an observation of the old format (before contract 2.0) is also accepted. Only the structure is
checked: whether the values match the image still needs a visual review.
"""

import argparse
from pathlib import Path

from .contract import parse_strict_json, validate_any, validate_observation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("path", type=Path)
    parser.add_argument("--require-v2", action="store_true", help="refuse the old format")
    args = parser.parse_args()
    obj, errors = parse_strict_json(args.path.read_text(encoding="utf-8"))
    if not errors:
        errors = (validate_observation if args.require_v2 else validate_any)(obj)
    if errors:
        print("FAIL\n" + "\n".join(errors))
        return 1
    print("PASS (structure only; visual review still required)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
