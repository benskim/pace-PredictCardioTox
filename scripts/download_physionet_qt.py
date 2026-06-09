#!/usr/bin/env python
"""Download the PhysioNet QT Database for local analytics validation."""

from __future__ import annotations

import argparse

from ecg_analytics.physionet import download_qt_database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/physionet", help="Base directory for PhysioNet data.")
    parser.add_argument("--records", nargs="*", help="Optional QT Database records, e.g. sel100 sel102.")
    parser.add_argument("--annotators", nargs="*", help="Optional annotators, e.g. pu0 pu1.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = download_qt_database(args.data_dir, records=args.records, annotators=args.annotators)
    print(f"QT Database files are available in: {target}")


if __name__ == "__main__":
    main()
