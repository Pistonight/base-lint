from os import listdir, access, W_OK
from os.path import isfile, isdir, join

def normalize_path(rel_path):
    if isfile(rel_path):
        if rel_path.endswith("/"):
            rel_path = rel_path[:-1]
        return True, rel_path
    elif isdir(rel_path):
        if not rel_path.endswith("/"):
            rel_path = rel_path + "/"
        return False, rel_path
    return None, None

class SuffixSet:
    underlying: set
    least: int
    most: int
    def __init__(self, input_set: set):
        self.underlying = input_set
        self.least = None
        self.most = None
        for s in input_set:
            self.least = len(s) if self.least is None else min(len(s),self.least)
            self.most = len(s) if self.most is None else max(len(s),self.most)

    def suffix_matches(self, input_string: str) -> bool:
        if not self.underlying:
            return False
        for l in range(self.least,self.most+1):
            suf = input_string[-l:]
            if suf in self.underlying:
                return True
        return False

def lint_path(rel_path, errors: list, *, verbose: bool, skip_binary: bool, ignore: SuffixSet, windows: SuffixSet, fix: bool):
    """Lint path (file or directory)"""
    is_file, rel_path = normalize_path(rel_path)
    if not rel_path:
        if verbose:
            print(f"Not file or dir: {rel_path}")
        return
    if ignore.suffix_matches(rel_path):
        if verbose:
            print(f"Ignoring: {rel_path}")
        return

    if is_file:
        is_windows = windows.suffix_matches(rel_path)
        if skip_binary:
            try:
                error = lint_file(rel_path, verbose=verbose, windows=is_windows, fix=fix)
                if error:
                    errors.append((rel_path, error))
            except UnicodeDecodeError:
                if verbose:
                    print(f"Binary: {rel_path}")
                return
        else:
            error = lint_file(rel_path, verbose=verbose, windows=is_windows, fix=fix)
            if error:
                errors.append((rel_path, error))
    else:
        for subpath in listdir(rel_path):
            lint_path(join(rel_path, subpath), errors, verbose=verbose, skip_binary=skip_binary, ignore=ignore, windows=windows, fix=fix)


def lint_file(file_path, *, verbose: bool, windows: bool, fix: bool):
    """Lint file"""
    if not access(file_path, W_OK):
        if verbose:
            print(f"Ignoring read-only file {file_path}")
        return
    if verbose:
        print(f"Checking {file_path}")
    errors = set()
    good_lines = []
    le = "\r\n" if windows else "\n"

    with open(file_path, 'r', encoding="utf-8", newline="") as file:
        last_line = None
        while True:
            line = file.readline()

            if not line:
                # End of file
                break
            last_line = line
            # Line ending
            if windows:
                if not line.endswith("\r\n"):
                    if fix:
                        line = line.replace("\n", "\r\n")
                    else:
                        errors.add("Line Ending (Expected \\r\\n)")
            else:
                if line.find("\r") != -1:
                    if fix:
                        line = line.replace("\r\n", "\n")
                    else:
                        errors.add("Line Ending (Expected \\n)")

            # Trailing space
            if len(line) >= len(le) and line.rstrip() != line[:-len(le)]:
                    if fix:
                        line = line.rstrip() + le
                    else:
                        errors.add("Trailing Whitespace")
            if fix:
                good_lines.append(line)

        if last_line is not None:
            if last_line[-1] != "\n":
                if fix:
                    good_lines.append(le)
                else:
                    errors.add("Needs trailing new line")
            elif last_line[0] in ("\n", "\r"):
                if fix:
                    while good_lines[-1][0] in ("\n", "\r"):
                        good_lines.pop()
                else:
                    errors.add("Too many trailing new lines")

    if fix:
        with open(file_path, 'w', encoding="utf-8", newline="") as file:
            file.writelines(good_lines)

    return errors
