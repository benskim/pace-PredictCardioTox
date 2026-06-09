#!/usr/bin/env python
"""Load a local PhysioNet QT Database record and print validation summaries."""

from __future__ import annotations

import argparse

from ecg_analytics.physionet import load_qt_annotations, load_qt_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", help="QT Database record name, e.g. sel100.")
    parser.add_argument("--data-dir", default="data/physionet", help="Base directory for PhysioNet data.")
    parser.add_argument("--annotator", default="pu0", help="Annotation extension to load.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    signals, metadata = load_qt_record(args.record, args.data_dir)
    annotations = load_qt_annotations(args.record, args.annotator, args.data_dir)
    print("Record metadata:")
    print(metadata)
    print("\nSignal preview:")
    print(signals.head())
    print("\nAnnotation counts:")
    print(annotations["symbol"].value_counts(dropna=False).head(20))


if __name__ == "__main__":
    main()
