import argparse
import json
from pathlib import Path
from .csvio import load_orders
from .money import calculate_totals
from .reports import summarize_orders


def main():
    parser = argparse.ArgumentParser(prog='cartkit')
    parser.add_argument('command', choices=['totals', 'summary', 'import-csv'])
    parser.add_argument('path', type=Path)
    args = parser.parse_args()
    if args.command == 'import-csv':
        with args.path.open(newline='') as source:
            result = load_orders(source.read())
    else:
        data = json.loads(args.path.read_text())
        if args.command == 'totals':
            result = calculate_totals(data)
        else:
            result = summarize_orders(data)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
