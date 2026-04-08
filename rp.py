#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# rp.py - Advanced grep-like tool with regex and statistics

VERSION = '5.1'

import sys
import re
import argparse
import os
import fnmatch
from typing import List, Tuple, Optional, Iterator
from collections import deque

# ANSI color codes
COLORS = [
    '\033[04;01;32m',  # green
    '\033[04;01;33m',  # yellow
    '\033[04;01;31m',  # red
    '\033[04;01;34m',  # blue
    '\033[0;04;35m',   # purple
    '\033[04;01;35m',  # magenta
    '\033[04;01;36m',  # cyan
    '\033[0;04;33m',   # brown
]
RESET = '\033[0m'
CONTEXT_COLOR = '\033[0;36m'  # cyan for context line markers


class Statistics:
    """
    Collect and display match statistics for each pattern.
    """
    def __init__(self, pattern_names: List[str]):
        self.pattern_names = pattern_names
        self.pattern_counts = {name: 0 for name in pattern_names}
        self.total_lines = 0
        self.matching_lines = 0
        
    def record_line(self, line_matches: bool, pattern_matches: List[int]):
        """
        Record statistics for a processed line.
        pattern_matches: list of pattern indices that matched
        """
        self.total_lines += 1
        if line_matches:
            self.matching_lines += 1
        
        for idx in pattern_matches:
            if idx < len(self.pattern_names):
                self.pattern_counts[self.pattern_names[idx]] += 1
    
    def display(self):
        """Display formatted statistics on stderr (to not pollute stdout pipelines)."""
        print(f"\n{COLORS[5]}=== Statistics ==={RESET}", file=sys.stderr)
        print(f"Total lines processed: {self.total_lines}", file=sys.stderr)
        print(f"Lines with matches: {self.matching_lines}", file=sys.stderr)

        if self.matching_lines > 0:
            percentage = (self.matching_lines / self.total_lines) * 100
            print(f"Match rate: {percentage:.2f}%", file=sys.stderr)

        print(f"\n{COLORS[3]}Pattern matches:{RESET}", file=sys.stderr)
        max_name_len = max(len(name) for name in self.pattern_names) if self.pattern_names else 0

        for i, name in enumerate(self.pattern_names):
            count = self.pattern_counts[name]
            color = COLORS[i % len(COLORS)]
            print(f"  {color}{name:<{max_name_len}}{RESET}: {count}", file=sys.stderr)


def load_patterns_from_file(filepath: str) -> List[str]:
    """
    Load patterns from file, one pattern per line.
    Ignores empty lines and lines starting with #.
    """
    if not os.path.isfile(filepath):
        print(f"Error: Pattern file '{filepath}' not found", file=sys.stderr)
        sys.exit(1)
    
    patterns = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                patterns.append(line)
        
        if not patterns:
            print(f"Error: No valid patterns found in {filepath}", file=sys.stderr)
            sys.exit(1)
        
        return patterns
    except (IOError, OSError) as e:
        print(f"Error reading pattern file {filepath}: {e}", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(f"Error: Pattern file {filepath} contains invalid UTF-8: {e}", file=sys.stderr)
        sys.exit(1)


def is_binary_file(filepath: str) -> bool:
    """
    Check if file is binary by reading first 8KB.
    Returns True if binary, False if text.
    """
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(8192)
            if b'\x00' in chunk:
                return True
            # Try to decode as UTF-8
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except (IOError, OSError):
        return True


def find_all_matches(line: str, patterns: List[Tuple[re.Pattern, str]]) -> List[Tuple[int, int, str, int]]:
    """
    Find all matches for all patterns in a line.
    Returns list of (start, end, color, pattern_idx) tuples.
    """
    matches = []
    for idx, (pattern, color) in enumerate(patterns):
        for match in pattern.finditer(line):
            matches.append((match.start(), match.end(), color, idx))
    
    # Sort by start position, then by end position (longer matches first)
    matches.sort(key=lambda x: (x[0], -x[1]))
    return matches


def apply_colors(line: str, matches: List[Tuple[int, int, str, int]]) -> Tuple[str, List[int]]:
    """
    Apply colors to line by inserting ANSI codes.
    Builds result left-to-right with list + join → O(n) instead of O(n·m).
    Returns (colored_line, list_of_matched_pattern_indices).
    """
    if not matches:
        return line, []

    # Remove overlapping matches (keep first/longest)
    filtered = []
    pattern_indices = []
    last_end = -1
    for start, end, color, idx in matches:
        if start >= last_end:
            filtered.append((start, end, color))
            if idx not in pattern_indices:
                pattern_indices.append(idx)
            last_end = end

    # Build result left-to-right — no position shifts, O(n) total allocations
    parts = []
    prev = 0
    for start, end, color in filtered:
        parts.append(line[prev:start])
        parts.append(color)
        parts.append(line[start:end])
        parts.append(RESET)
        prev = end
    parts.append(line[prev:])

    return ''.join(parts), pattern_indices


def has_match(line: str, patterns: List[re.Pattern]) -> bool:
    """Check if line contains any pattern."""
    return any(pattern.search(line) for pattern in patterns)


def extract_only_matches(line: str, patterns: List[Tuple[re.Pattern, str]]) -> Tuple[List[str], List[int]]:
    """
    Extract only the matching parts from the line, de-overlapping like apply_colors.
    Returns (list of colored match strings, list of pattern indices).
    """
    all_matches = []
    for idx, (pattern, color) in enumerate(patterns):
        for match in pattern.finditer(line):
            all_matches.append((match.start(), match.end(), color, idx, match.group()))

    if not all_matches:
        return [], []

    all_matches.sort(key=lambda x: (x[0], -x[1]))

    results = []
    pattern_indices = []
    last_end = -1
    for start, end, color, idx, text in all_matches:
        if start >= last_end:
            results.append(f"{color}{text}{RESET}")
            if idx not in pattern_indices:
                pattern_indices.append(idx)
            last_end = end

    return results, pattern_indices


class ContextBuffer:
    """
    Manages context lines before and after matches.
    """
    def __init__(self, before: int, after: int):
        self.before = before
        self.after = after
        self.before_buffer = deque(maxlen=before if before > 0 else 1)
        self.after_counter = 0
        self.last_was_match = False
        self.last_printed = -1  # tracks last printed line_num; replaces unbounded set

    def process_line(self, line_num: int, line: str, is_match: bool,
                     show_line_numbers: bool) -> List[Tuple[str, str]]:
        """
        Process a line and return lines to print.
        Returns list of (prefix, line) tuples. Includes '--' separators between
        non-adjacent context groups (like grep).
        """
        output = []

        if is_match:
            # Determine first line of this context group
            first_in_group = line_num
            if self.before > 0:
                for buf_num, _ in self.before_buffer:
                    if buf_num > self.last_printed:
                        first_in_group = buf_num
                        break

            # Emit '--' separator between non-adjacent groups
            if self.last_printed >= 0 and first_in_group > self.last_printed + 1:
                output.append(('', '--'))

            # Before-context
            if self.before > 0:
                for buf_num, buf_line in self.before_buffer:
                    if buf_num > self.last_printed:
                        prefix = self._format_prefix(buf_num, '-', show_line_numbers)
                        output.append((prefix, buf_line))
                        self.last_printed = buf_num

            # Match line
            prefix = self._format_prefix(line_num, ':', show_line_numbers)
            output.append((prefix, line))
            self.last_printed = line_num

            self.after_counter = self.after
            self.last_was_match = True
        elif self.after_counter > 0:
            # After-context
            prefix = self._format_prefix(line_num, '-', show_line_numbers)
            output.append((prefix, line))
            self.last_printed = line_num
            self.after_counter -= 1
        else:
            # Not a match, not in after-context: buffer for potential before-context
            if self.before > 0:
                self.before_buffer.append((line_num, line))

        return output
    
    def _format_prefix(self, line_num: int, separator: str, show_line_numbers: bool) -> str:
        """Format line number prefix with separator."""
        if show_line_numbers:
            return f"{CONTEXT_COLOR}{line_num}{separator}{RESET}"
        return ""


def process_stream(stream: Iterator[str], args, patterns_with_colors, patterns_only,
                   stats: Optional[Statistics] = None, filename: str = '') -> int:
    """
    Process input stream and return match count.
    Single regex scan per line: find_all_matches once, apply_colors at most once.
    filename: prepended to each output line (for -H mode); empty = no prefix.
    """
    match_count = 0
    context_buffer = ContextBuffer(args.before_context, args.after_context)
    fn_prefix = f"{filename}:" if filename else ""

    # Modes that suppress line output and just count (-c, -q, -l, -L)
    suppress_output = (
        args.count or
        args.quiet or
        args.files_with_matches or
        args.files_without_match
    )

    for line_num, line in enumerate(stream, start=1):
        line = line.rstrip('\r\n')

        # --- Single scan per line ---
        if args.invert_match:
            # Short-circuit: only need bool, no colorization for inverted output
            line_matches = not has_match(line, patterns_only)
            colored_line = line
            pattern_indices = []
        else:
            matches = find_all_matches(line, patterns_with_colors)
            line_matches = bool(matches)
            if line_matches and not (suppress_output and not stats):
                # Colorize once — colored_line for output, pattern_indices for stats
                colored_line, pattern_indices = apply_colors(line, matches)
            else:
                colored_line = line
                pattern_indices = []

        if stats:
            stats.record_line(line_matches, pattern_indices)

        # Suppress-output modes (-c, -q, -l, -L): just count, no line printing
        if suppress_output:
            if line_matches or args.display_all:
                match_count += 1
                # Quiet: exit immediately on first match (unless collecting stats)
                if args.quiet and not stats:
                    return match_count
                # Max-count
                if args.max_count > 0 and match_count >= args.max_count:
                    break
            continue

        # Only matching mode
        if args.only_matching and not args.invert_match:
            if line_matches or args.display_all:
                matches_only, _ = extract_only_matches(line, patterns_with_colors)
                for match_str in matches_only:
                    if args.line_number:
                        print(f"{fn_prefix}{line_num}:{match_str}")
                    else:
                        print(f"{fn_prefix}{match_str}")
                    match_count += 1
            continue

        # Normal output mode
        if line_matches or args.display_all:
            match_count += 1
            if args.before_context > 0 or args.after_context > 0:
                lines_to_print = context_buffer.process_line(
                    line_num, colored_line, line_matches, args.line_number
                )
                for ctx_prefix, output_line in lines_to_print:
                    if output_line == '--':
                        print('--')  # separator: no filename prefix
                    else:
                        print(f"{fn_prefix}{ctx_prefix}{output_line}")
            else:
                if args.line_number:
                    print(f"{fn_prefix}{line_num}:{colored_line}")
                else:
                    print(f"{fn_prefix}{colored_line}")
            # Max-count in normal mode
            if args.max_count > 0 and match_count >= args.max_count:
                break
        else:
            if args.before_context > 0 or args.after_context > 0:
                context_buffer.process_line(line_num, line, False, args.line_number)

    return match_count


def scan_files(paths: List[str], args) -> Iterator[Tuple[str, Iterator[str]]]:
    """
    Scan files and directories, yielding (filepath, line_iterator) tuples.
    Handles recursive scanning and binary file filtering.
    """
    for path in paths:
        if not os.path.exists(path):
            print(f"Error: {path}: No such file or directory", file=sys.stderr)
            continue
            
        if os.path.isfile(path):
            # Skip binary files if requested
            if args.no_binary and is_binary_file(path):
                if not args.count and not args.stats:
                    print(f"Binary file {path} matches (skipped)", file=sys.stderr)
                continue
            
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    yield (path, f)
            except PermissionError:
                print(f"Permission denied: {path}", file=sys.stderr)
            except (IOError, OSError) as e:
                print(f"Error reading {path}: {e}", file=sys.stderr)
                
        elif os.path.isdir(path):
            if args.recursive:
                for root, dirs, files in os.walk(path):
                    # Skip hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    for filename in files:
                        if filename.startswith('.'):
                            continue

                        # --include / --exclude glob filters (recursive mode only)
                        if args.include and not any(fnmatch.fnmatch(filename, p) for p in args.include):
                            continue
                        if args.exclude and any(fnmatch.fnmatch(filename, p) for p in args.exclude):
                            continue

                        filepath = os.path.join(root, filename)

                        if args.no_binary and is_binary_file(filepath):
                            continue

                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                                yield (filepath, f)
                        except (IOError, OSError, PermissionError):
                            continue
            else:
                print(f"Error: {path} is a directory (use -r for recursive)", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Search and highlight patterns in text with regex support.",
        formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(
            prog, max_help_position=36
        ),
        epilog="""
Examples:
  cat file.log | %(prog)s error warning
  %(prog)s "ERROR|WARN" file.log
  %(prog)s -r -i "exception" /var/log/
  %(prog)s -n -C 3 "pattern" file.txt
  %(prog)s --stats -f patterns.txt access.log
        """
    )
    
    # Positional arguments — patterns first, then files/dirs
    # Argparse can't split two nargs='*' correctly, so we use one list
    # and split manually after parsing (trailing existing paths = files).
    parser.add_argument(
        "positionals",
        nargs='*',
        metavar="PATTERN|FILE",
        help="Search patterns followed by files/directories (stdin if no files given)"
    )

    # Explicit pattern specification (overrides positional heuristic)
    parser.add_argument(
        "-e", "--regexp",
        action="append",
        dest="regexp",
        metavar="PATTERN",
        help="Explicit search pattern (can repeat; all positionals become files)"
    )

    # Basic options
    parser.add_argument(
        "-i", "--ignore-case", 
        action="store_true", 
        help="Ignore case distinctions in patterns"
    )
    parser.add_argument(
        "-k", "--display-all", 
        action="store_true", 
        help="Display all lines, only highlight matches"
    )
    parser.add_argument(
        "-v", "--invert-match", 
        action="store_true", 
        help="Select non-matching lines"
    )
    parser.add_argument(
        "-w", "--word-regexp", 
        action="store_true", 
        help="Match only whole words"
    )
    
    # Output control
    parser.add_argument(
        "-n", "--line-number", 
        action="store_true", 
        help="Print line numbers with output"
    )
    parser.add_argument(
        "-c", "--count", 
        action="store_true", 
        help="Print only count of matching lines"
    )
    parser.add_argument(
        "-o", "--only-matching",
        action="store_true",
        help="Print only matched parts of lines"
    )
    parser.add_argument(
        "-H", "--with-filename",
        action="store_true",
        help="Always print filename prefix on output lines"
    )
    parser.add_argument(
        "--no-filename",
        action="store_true",
        help="Never print filename prefix on output lines"
    )
    parser.add_argument(
        "-Z", "--null",
        action="store_true",
        help="Print null byte after each filename (for use with xargs -0)"
    )

    # Context control
    parser.add_argument(
        "-A", "--after-context", 
        type=int, 
        default=0, 
        metavar="NUM",
        help="Print NUM lines of trailing context"
    )
    parser.add_argument(
        "-B", "--before-context", 
        type=int, 
        default=0, 
        metavar="NUM",
        help="Print NUM lines of leading context"
    )
    parser.add_argument(
        "-C", "--context", 
        type=int, 
        metavar="NUM",
        help="Print NUM lines of output context"
    )
    
    # File handling
    parser.add_argument(
        "-r", "--recursive", 
        action="store_true", 
        help="Read all files under each directory, recursively"
    )
    parser.add_argument(
        "-I", "--no-binary", 
        action="store_true", 
        help="Skip binary files"
    )
    
    # Advanced features
    parser.add_argument(
        "-f", "--file",
        action="append",
        dest="pattern_files",
        metavar="FILE",
        help="Read patterns from FILE, one per line (can be repeated)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display statistics about pattern matches (written to stderr)"
    )
    parser.add_argument(
        "-l", "--files-with-matches",
        action="store_true",
        help="Print only names of files containing matches"
    )
    parser.add_argument(
        "-L", "--files-without-match",
        action="store_true",
        help="Print only names of files containing no matches"
    )
    parser.add_argument(
        "-m", "--max-count",
        type=int,
        default=0,
        metavar="NUM",
        help="Stop after NUM matches per file (0 = unlimited)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output; exit 0 if any match found"
    )
    parser.add_argument(
        "--include",
        action="append",
        metavar="GLOB",
        help="Search only files matching GLOB (can be repeated, e.g. '*.log')"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        metavar="GLOB",
        help="Skip files matching GLOB (can be repeated)"
    )
    parser.add_argument(
        "--color",
        choices=["always", "never", "auto"],
        default="auto",
        metavar="WHEN",
        help="Colorize output: always, never, or auto (default: auto)"
    )
    parser.add_argument(
        "--line-buffered",
        action="store_true",
        help="Force line-buffered output (useful for tail -f pipelines)"
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {VERSION}"
    )

    args = parser.parse_args()

    # Color mode (F1): auto = use color only when stdout is a TTY and NO_COLOR not set
    use_color = (
        args.color == 'always' or
        (args.color == 'auto' and sys.stdout.isatty() and 'NO_COLOR' not in os.environ)
    )
    if not use_color:
        global RESET, CONTEXT_COLOR
        COLORS[:] = ['' for _ in COLORS]
        RESET = ''
        CONTEXT_COLOR = ''

    # Stdout buffering (P6/F8): line-buffered on demand, default block-buffering otherwise
    if args.line_buffered and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)

    # Handle -C option (sets both -A and -B)
    if args.context is not None:
        if args.before_context != 0 or args.after_context != 0:
            print("Warning: -C overrides -A/-B", file=sys.stderr)
        args.before_context = args.context
        args.after_context = args.context
    
    # Validate arguments
    if args.before_context < 0 or args.after_context < 0:
        print("Error: Context values must be non-negative", file=sys.stderr)
        sys.exit(1)
    
    # Split positionals into patterns and files.
    # -e flag: all positionals are files; patterns come from -e only.
    # Otherwise: heuristic — scan from right, collect trailing existing paths as files.
    positionals = args.positionals
    if args.regexp:
        patterns_from_args = []
        files_to_search = positionals
    else:
        file_start = len(positionals)
        for i in range(len(positionals) - 1, -1, -1):
            if os.path.exists(positionals[i]):
                file_start = i
            else:
                break
        patterns_from_args = positionals[:file_start]
        files_to_search = positionals[file_start:]

    # Load patterns from file(s) if specified
    searchterms = []
    if args.pattern_files:
        for pf in args.pattern_files:
            searchterms.extend(load_patterns_from_file(pf))

    # -e / --regexp patterns
    if args.regexp:
        searchterms.extend(args.regexp)

    # Patterns from positionals (when -e not used)
    searchterms.extend(patterns_from_args)

    # Validate that we have at least one pattern
    if not searchterms:
        print("Error: No search patterns specified. Use patterns as arguments or -f FILE", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    # Add word boundaries if -w is set
    if args.word_regexp:
        searchterms = [rf"\b{term}\b" for term in searchterms]
    
    # Compile regex patterns
    flags = re.IGNORECASE if args.ignore_case else 0
    patterns_with_colors = []
    patterns_only = []
    
    for i, term in enumerate(searchterms):
        try:
            compiled = re.compile(term, flags)
            patterns_with_colors.append((compiled, COLORS[i % len(COLORS)]))
            patterns_only.append(compiled)
        except re.error as e:
            print(f"Error: Invalid regex pattern '{term}': {e}", file=sys.stderr)
            sys.exit(1)
    
    # Initialize statistics if requested
    stats = Statistics(searchterms) if args.stats else None
    
    total_matches = 0
    
    # Process files or stdin
    if files_to_search:
        # File mode
        multiple_files = len(files_to_search) > 1 or (
            len(files_to_search) == 1 and
            os.path.isdir(files_to_search[0]) and
            args.recursive
        )

        # -H: per-line filename prefix (replaces section headers)
        # -h: suppress all filename output
        # default: section headers for multiple files, no per-line prefix
        if args.with_filename:
            show_filename_prefix = True
        elif args.no_filename:
            show_filename_prefix = False
        else:
            show_filename_prefix = False

        show_header = (
            multiple_files and
            not args.count and
            not args.stats and
            not args.quiet and
            not args.files_with_matches and
            not args.files_without_match and
            not args.with_filename  # -H replaces section headers with per-line prefix
        )

        for filepath, stream in scan_files(files_to_search, args):
            if show_header:
                print(f"\n{COLORS[5]}=== {filepath} ==={RESET}")

            match_count = process_stream(
                stream, args, patterns_with_colors, patterns_only, stats,
                filename=filepath if show_filename_prefix else ''
            )
            total_matches += match_count

            # -l / -L: print filename (--null/-Z uses NUL separator for xargs -0)
            if args.files_with_matches and match_count > 0:
                if args.null:
                    sys.stdout.write(filepath + '\0')
                else:
                    print(filepath)
            elif args.files_without_match and match_count == 0:
                if args.null:
                    sys.stdout.write(filepath + '\0')
                else:
                    print(filepath)

            # -c: per-file count output
            if args.count:
                if multiple_files:
                    print(f"{filepath}:{match_count}")
                else:
                    print(match_count)

            # -q: exit as soon as any file has a match
            if args.quiet and total_matches > 0:
                break
    else:
        # Stdin mode
        match_count = process_stream(sys.stdin, args, patterns_with_colors, patterns_only, stats)

        if args.count:
            print(match_count)

        total_matches = match_count

    # Display statistics if requested
    if args.stats:
        stats.display()
        if args.count:
            print(f"\nTotal matches: {total_matches}", file=sys.stderr)
    
    # Exit code: 0 if matches found, 1 if no matches
    sys.exit(0 if total_matches > 0 else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except BrokenPipeError:
        # Handle broken pipe (e.g., piping to head)
        # Python flushes on exit, which can cause a second BrokenPipeError
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(141)
