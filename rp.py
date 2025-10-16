#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# rp.py - Advanced grep-like tool with regex and statistics

import sys
import re
import argparse
import os
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
        """Display formatted statistics."""
        print(f"\n{COLORS[5]}=== Statistics ==={RESET}")
        print(f"Total lines processed: {self.total_lines}")
        print(f"Lines with matches: {self.matching_lines}")
        
        if self.matching_lines > 0:
            percentage = (self.matching_lines / self.total_lines) * 100
            print(f"Match rate: {percentage:.2f}%")
        
        print(f"\n{COLORS[3]}Pattern matches:{RESET}")
        max_name_len = max(len(name) for name in self.pattern_names) if self.pattern_names else 0
        
        for name in self.pattern_names:
            count = self.pattern_counts[name]
            color = COLORS[self.pattern_names.index(name) % len(COLORS)]
            print(f"  {color}{name:<{max_name_len}}{RESET}: {count}")


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
            for line_num, line in enumerate(f, start=1):
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
    Process from right to left to avoid position shifts.
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
    
    # Apply colors from right to left
    result = line
    for start, end, color in reversed(filtered):
        result = result[:start] + color + result[start:end] + RESET + result[end:]
    
    return result, pattern_indices


def has_match(line: str, patterns: List[re.Pattern]) -> bool:
    """Check if line contains any pattern."""
    return any(pattern.search(line) for pattern in patterns)


def extract_only_matches(line: str, patterns: List[Tuple[re.Pattern, str]]) -> Tuple[List[str], List[int]]:
    """
    Extract only the matching parts from the line.
    Returns (list of colored match strings, list of pattern indices).
    """
    results = []
    pattern_indices = []
    for idx, (pattern, color) in enumerate(patterns):
        for match in pattern.finditer(line):
            colored_match = f"{color}{match.group()}{RESET}"
            results.append(colored_match)
            if idx not in pattern_indices:
                pattern_indices.append(idx)
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
        self.printed_lines = set()
        
    def process_line(self, line_num: int, line: str, is_match: bool, 
                    show_line_numbers: bool) -> List[Tuple[str, str]]:
        """
        Process a line and return lines to print.
        Returns list of (prefix, line) tuples.
        """
        output = []
        
        if is_match:
            # Print buffered before-context if not already printed
            if self.before > 0:
                for buf_num, buf_line in self.before_buffer:
                    if buf_num not in self.printed_lines:
                        prefix = self._format_prefix(buf_num, '-', show_line_numbers)
                        output.append((prefix, buf_line))
                        self.printed_lines.add(buf_num)
            
            # Print the match line
            prefix = self._format_prefix(line_num, ':', show_line_numbers)
            output.append((prefix, line))
            self.printed_lines.add(line_num)
            
            self.after_counter = self.after
            self.last_was_match = True
        elif self.after_counter > 0:
            # Print after-context
            prefix = self._format_prefix(line_num, '-', show_line_numbers)
            output.append((prefix, line))
            self.printed_lines.add(line_num)
            self.after_counter -= 1
        else:
            # Add to before-context buffer
            if self.before > 0:
                self.before_buffer.append((line_num, line))
        
        return output
    
    def _format_prefix(self, line_num: int, separator: str, show_line_numbers: bool) -> str:
        """Format line number prefix with separator."""
        if show_line_numbers:
            return f"{CONTEXT_COLOR}{line_num}{separator}{RESET}"
        return ""


def process_stream(stream: Iterator[str], args, patterns_with_colors, patterns_only, stats: Optional[Statistics] = None) -> int:
    """
    Process input stream and return match count.
    """
    match_count = 0
    context_buffer = ContextBuffer(args.before_context, args.after_context)
    
    for line_num, line in enumerate(stream, start=1):
        line = line.rstrip('\n')
        
        # Check if line matches
        line_matches = has_match(line, patterns_only)
        
        # Find which patterns matched (for statistics)
        pattern_indices = []
        if line_matches and stats and not args.invert_match:
            matches = find_all_matches(line, patterns_with_colors)
            _, pattern_indices = apply_colors(line, matches)
        
        # Apply invert match logic
        if args.invert_match:
            line_matches = not line_matches
            # For inverted matches, we don't track pattern statistics
            pattern_indices = []
        
        # Record statistics for this line (only once per line)
        if stats:
            stats.record_line(line_matches, pattern_indices)
        
        # Count mode: just count matches
        if args.count:
            if line_matches or args.display_all:
                match_count += 1
            continue
        
        # Only matching mode: extract and print only matches
        if args.only_matching and not args.invert_match:
            if line_matches or args.display_all:
                matches_only, _ = extract_only_matches(line, patterns_with_colors)
                for match_str in matches_only:
                    if args.line_number:
                        print(f"{line_num}:{match_str}")
                    else:
                        print(match_str)
                    match_count += 1
            continue
        
        # Normal mode: highlight and print lines
        if line_matches or args.display_all:
            match_count += 1
            
            # Find and apply colors
            matches = find_all_matches(line, patterns_with_colors)
            colored_line, _ = apply_colors(line, matches)
            
            # Handle context
            if args.before_context > 0 or args.after_context > 0:
                lines_to_print = context_buffer.process_line(
                    line_num, colored_line, line_matches, args.line_number
                )
                for prefix, output_line in lines_to_print:
                    print(f"{prefix}{output_line}")
            else:
                # No context: simple print
                if args.line_number:
                    print(f"{line_num}:{colored_line}")
                else:
                    print(colored_line)
        else:
            # Not a match, but might need for context
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
            except (IOError, OSError) as e:
                print(f"Error reading {path}: {e}", file=sys.stderr)
            except PermissionError:
                print(f"Permission denied: {path}", file=sys.stderr)
                
        elif os.path.isdir(path):
            if args.recursive:
                for root, dirs, files in os.walk(path):
                    # Skip hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    for filename in files:
                        if filename.startswith('.'):
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cat file.log | %(prog)s error warning
  %(prog)s "ERROR|WARN" file.log
  %(prog)s -r -i "exception" /var/log/
  %(prog)s -n -C 3 "pattern" file.txt
  %(prog)s --stats -f patterns.txt access.log
        """
    )
    
    # Positional arguments
    parser.add_argument(
        "searchterms", 
        nargs='*', 
        help="Search patterns (regex supported)"
    )
    parser.add_argument(
        "files", 
        nargs='*', 
        help="Files to search (default: stdin)"
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
        metavar="FILE",
        help="Read patterns from FILE, one per line"
    )
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="Display statistics about pattern matches"
    )
    
    args = parser.parse_args()
    
    # Handle -C option (sets both -A and -B)
    if args.context is not None:
        args.before_context = args.context
        args.after_context = args.context
    
    # Validate arguments
    if args.before_context < 0 or args.after_context < 0:
        print("Error: Context values must be non-negative", file=sys.stderr)
        sys.exit(1)
    
    # Load patterns from file if specified
    searchterms = []
    if args.file:
        searchterms = load_patterns_from_file(args.file)
    
    # Add command-line patterns
    if args.searchterms:
        searchterms.extend(args.searchterms)
    
    # Validate that we have at least one pattern
    if not searchterms:
        print("Error: No search patterns specified. Use patterns as arguments or -f FILE", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    # Files to search are in args.files
    files_to_search = args.files if args.files else []
    
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
        
        for filepath, stream in scan_files(files_to_search, args):
            if multiple_files and not args.count and not args.stats:
                print(f"\n{COLORS[5]}=== {filepath} ==={RESET}")
            
            match_count = process_stream(stream, args, patterns_with_colors, patterns_only, stats)
            
            if args.count:
                if multiple_files:
                    print(f"{filepath}:{match_count}")
                else:
                    print(match_count)
            
            total_matches += match_count
    else:
        # Stdin mode
        match_count = process_stream(sys.stdin, args, patterns_with_colors, patterns_only, stats)
        
        if args.count and not args.stats:
            print(match_count)
        
        total_matches = match_count
    
    # Display statistics if requested
    if args.stats:
        stats.display()
        if args.count:
            print(f"\nTotal matches: {total_matches}")
    
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
        import os
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(141)
