from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import ROOT, load_config, resolve_journal, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve journal information for one markdown file.")
    parser.add_argument("markdown")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--out")
    args = parser.parse_args()

    config = load_config(ROOT / args.config)
    result = resolve_journal((ROOT / args.markdown).resolve(), config)
    if args.out:
        write_json(ROOT / args.out, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
