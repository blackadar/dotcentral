#!/usr/bin/env python3
# Jordan Blackadar <blackadar@photodiagnostic.com>
import argparse
import pathlib
import re
from datetime import datetime


def main(version, output):
    working_dir = pathlib.Path('.').resolve()
    with open(f'{output}', 'w') as out:
        out.write(f"# v{version} Release Notes\n\n")
        for file in working_dir.rglob("release_notes.txt"):
            package = file.parent.name
            print(f"Translating {package}...")
            out.write(f"{package}\n")
            out.write(('-' * 16) + "\n")
            with open(file, 'r') as notes:
                matches = re.findall(
                        r'\* (\w+ \w+ \d+ \d+) (\w+\s*\w*) <(\w+@photodiagnostic.com)>\s*-\s*(\d+.\d+.\d+.\d+)\n([^*]*)',
                        notes.read())
                matches.sort(key=lambda x: datetime.strptime(x[0], "%a %b %d %Y"), reverse=True)
                for match in matches:
                    out.write(f"> {match[3]}\n")
                    out.write(f"> {match[0]}\n")
                    out.write(f"> {match[1]} <{match[2]}>\n")
                    out.write(f"{match[4]}\n\n")
    print(f"Done. Check {output}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Release Note Compilation Tool")
    parser.add_argument('version', type=str, nargs=1, help='cumulative release version for top of file')
    parser.add_argument('output', type=str, nargs='?', default='release_notes.md', help='file to output markdown to')
    args = parser.parse_args()
    main(args.version[0], args.output)
