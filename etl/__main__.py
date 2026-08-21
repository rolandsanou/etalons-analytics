import argparse
import sys

from . import extract, load, quality, transform


def main():
    ap = argparse.ArgumentParser(prog="etl", description="Étalons Analytics ETL")
    ap.add_argument("step", nargs="?", default="all",
                    choices=["all", "extract", "transform", "load", "quality"])
    ap.add_argument("--force", action="store_true",
                    help="re-download sources (extract step)")
    args = ap.parse_args()

    fails = 0
    if args.step in ("all", "extract"):
        extract.run(force=args.force)
    if args.step in ("all", "transform"):
        transform.run()
    if args.step in ("all", "load"):
        load.run()
    if args.step in ("all", "quality"):
        fails = quality.run()
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
