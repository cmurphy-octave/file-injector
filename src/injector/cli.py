from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


class MissingFilesError(Exception):
    def __init__(self, paths: set[Path]):
        self.paths = sorted(paths)

    def __str__(self) -> str:
        files = "\n".join(
            f"  {path}"
            for path in self.paths
        )

        return (
            "The following referenced files could not be found:\n\n"
            f"{files}"
        )

PLACEHOLDER_RE = re.compile(
    r"\$\{file:([^}]+)\}"
)


def inject(
    value: Any,
    base_dir: Path,
    missing_files: set[Path],
) -> Any:
    if isinstance(value, dict):
        return {
            k: inject(v, base_dir, missing_files)
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [
            inject(v, base_dir, missing_files)
            for v in value
        ]

    if isinstance(value, str):

        def replace(match: re.Match[str]) -> str:
            relative_path = Path(match.group(1))
            source_file = base_dir / relative_path

            if not source_file.is_file():
                missing_files.add(
                    relative_path.as_posix()
                )
                return match.group(0)

            return source_file.read_text(
                encoding="utf-8"
            )

        return PLACEHOLDER_RE.sub(replace, value)

    return value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inject external files into a JSON template."
    )

    parser.add_argument(
        "template",
        help="Input JSON template",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output JSON file",
    )

    args = parser.parse_args()

    template_path = Path(args.template).resolve()

    with template_path.open(
        encoding="utf-8"
    ) as f:
        document = json.load(f)

    missing_files: set[Path] = set()

    result = inject(
        document,
        template_path.parent,
        missing_files,
    )

    if missing_files:
        raise MissingFilesError(missing_files)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = template_path.with_name(
            f"{template_path.stem}.generated{template_path.suffix}"
        )

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