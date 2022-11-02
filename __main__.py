import argparse, toml, sys, os
from common import COMMON_IGNORE, COMMON_WINDOWS
from lint import lint_path, SuffixSet

EXAMPLES = """
examples:
  Current folder with common ignores
    basic-lint . -c
  scripts folder with common ignores and ignore file or directories that ends with .txt
    basic-lint scripts -c -i .txt
  ignore directory that ends with build but not files
    basic-lint . -i build/
  ignore directory named build
    basic-lint . -i /build/
  fix reported problems if possible
    basic-lint . -f

"""
parser = argparse.ArgumentParser(
    prog = "basic-lint",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description = "Common linter for piston projects",
    epilog = EXAMPLES)

parser.add_argument(
    "input",
    nargs="*",
    help="File or root directory to lint")
parser.add_argument(
    "-i",
    "--ignore",
    metavar="SUFFIX",
    action="append",
    help="Add a suffix to ignore")
parser.add_argument(
    "-a",
    "--add",
    metavar="SUFFIX",
    action="append",
    help="Remove a suffix from (common) ignore list")
parser.add_argument(
    "-b",
    "--binary-ignore",
    action="store_true",
    help="Ignore UnicodeDecodeError. By default, binary files will give an error. It's recommended that they are manually ignored so lint is faster")
parser.add_argument(
    "-p",
    "--profile",
    metavar="FILE",
    action="append",
    help="add a toml config profile")
parser.add_argument(
    "-c",
    "--common",
    action="store_true",
    help="Append common config")
parser.add_argument(
    "--show-common",
    action="store_true",
    help="Show the common config used by -c")
parser.add_argument(
    "-w",
    "--windows",
    metavar="SUFFIX",
    action="append",
    help="Enforce windows line ending instead of unix for the suffix")
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Print all processed files and detail info")
parser.add_argument(
    "-f",
    "--fix",
    action="store_true",
    help="Automatically fix problems if possible")


args = parser.parse_args()

if args.show_common:
    data = {
        "ignore": COMMON_IGNORE,
        "windows": COMMON_WINDOWS
    }
    print(toml.dumps(data))
    sys.exit(0)

if not args.input:
    print("Need at least 1 input file or directory")
    sys.exit(1)

ignores = set()
windows_files = set()

if args.ignore:
    for ignore in args.ignore:
        ignores.add(ignore)
if args.add:
    for add in args.add:
        ignores.remove(add)
if args.windows:
    for windows in args.windows:
        windows_files.add(windows)
if args.profile:
    for profile in args.profile:
        with open(profile, "r", encoding="utf-8") as toml_file:
            data = toml.load(toml_file)
        if "ignore" in data and data["ignore"]:
            for ignore in data["ignore"]:
                ignores.add(ignore)
        if "windows" in data and data["windows"]:
            for windows in data["windows"]:
                windows_files.add(windows)
        if "add" in data and data["add"]:
            for add in data["add"]:
                ignores.remove(add)
if args.common:
    for ignore in COMMON_IGNORE:
        ignores.add(ignore)
    for windows in COMMON_WINDOWS:
        windows_files.add(windows)

errors = []
for input_path in args.input:
    input_path = input_path.replace("\\", "/")
    if input_path == ".":
        input_path = "./"
    if not input_path.startswith("./"):
        input_path = os.path.join("./", input_path)

    lint_path(input_path, errors, verbose=args.verbose, skip_binary=args.binary_ignore, ignore=SuffixSet(ignores), windows=SuffixSet(windows_files), fix=args.fix)

if not errors:
    sys.exit(0)

for rel_path, suberrors in errors:
    if len(suberrors) > 1:
        print(f"{rel_path}:")
        for suberror in suberrors:
            print(f"  {suberror}")
    else:
        suberror = "".join(suberrors)
        print(f"{rel_path}: {suberror}")

sys.exit(1)
