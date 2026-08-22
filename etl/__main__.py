import argparse
import sys

from . import extract, load, quality, transform


def main():
    ap = argparse.ArgumentParser(prog="etl", description="Étalons Analytics ETL")
    ap.add_argument("step", nargs="?", default="all",
                    choices=["all", "extract", "transform", "load", "pages", "quality"])
    ap.add_argument("--force", action="store_true",
                    help="re-download every source that can change (extract step)")
    ap.add_argument("--force-profiles", action="store_true",
                    help="re-read player profiles and club form only: club, "
                         "league, market value and contract. Use this after a "
                         "transfer window — the profile cache is otherwise kept "
                         "for 30 days (extract step)")
    args = ap.parse_args()

    fails = 0
    if args.step in ("all", "extract"):
        extract.run(force=args.force, force_profiles=args.force_profiles)
    if args.step in ("all", "transform"):
        transform.run()
    if args.step in ("all", "load"):
        load.run()
    if args.step in ("all", "pages"):
        # the site generator lives in tools/ because it is a build step, not ETL
        import subprocess
        from .config import ROOT
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_site.py")],
                       check=True)
    if args.step in ("all", "quality"):
        fails = quality.run()
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
