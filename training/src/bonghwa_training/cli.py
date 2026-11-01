import argparse
from pathlib import Path

from bonghwa_training.build import build_dataset, verify_dataset
from bonghwa_training.download import download_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="산불 학습 자료 수집·변환·검증")
    commands = parser.add_subparsers(dest="command", required=True)
    download = commands.add_parser("download")
    download.add_argument("--destination", type=Path, required=True)
    selection = download.add_mutually_exclusive_group()
    selection.add_argument("--shards-per-split", type=int, default=1)
    selection.add_argument("--all-shards", action="store_true")
    build = commands.add_parser("build")
    build.add_argument("--raw", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "download":
        download_dataset(args.destination, None if args.all_shards else args.shards_per_split)
    elif args.command == "build":
        build_dataset(args.raw, args.output)
    elif args.command == "verify":
        verify_dataset(args.output)


if __name__ == "__main__":
    main()
