import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", help="Path to the config base folder")
args = parser.parse_args()
if args.config:
    CONFIG_BASE_PATH = Path(args.config)
