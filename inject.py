#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PLACEHOLDER_RE = re.compile(
    r"^\$\{file:(.+)\}$"
)


def inject(
    value: Any,
    base_dir: Path,
) -> Any:
    """
    Recursively traverse a JSON structure and replace
    placeholders of the form:

        ${file:path/to/file.ext}

    with the contents of the referenced file.
    """

    if isinstance(value, dict):
        return {
            k: inject(v, base_dir)
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [
            inject(v, base_dir)
            for v in value
        ]

    if isinstance(value, str):
        match = PLACEHOLDER_RE.fullmatch(value)

        if match:
            relative_path = Path(match.group(1))
            source_file = base_dir / relative_path

            if not source_file.exists():
                raise FileNotFoundError(
                    f"Referenced file does not exist: "
                    f"{source_file}"
                )

            return source_file.read_text(
                encoding="utf-8"
            )

    return value


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Inject external text files into a JSON template."
        )
    )

    parser.add_argument(
        "template",
        help="Input JSON template",
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output JSON file",
    )

    args = parser.parse_args()

    template_path = Path(args.template).resolve()

    with template_path.open(
        encoding="utf-8"
    ) as f:
        document = json.load(f)

    result = inject(
        document,
        template_path.parent,
    )

    output_path = Path(args.output)

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")


if __name__ == "__main__":
    main()