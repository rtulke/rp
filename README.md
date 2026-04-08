rp
==

rp (red pencil) is a command-line tool for searching and highlighting text with multi-pattern support, regex, and match statistics. Each search pattern gets its own color, making it easy to visually distinguish multiple patterns at once in log files, source code, and any text output.

![Example](/images/rpen1.png)


## Features

- Multi-color highlighting with up to 8 distinct colors per pattern
- Full regular expression support
- Single-pass processing for efficient multi-pattern search
- Statistics mode with per-pattern match counts
- Context lines before and after matches, with group separators
- Recursive directory search with glob-based file filtering
- Multiple output modes: count, only-matching, invert, files-with-matches
- Filename prefix control and null-separated output for scripting
- Color auto-detection based on TTY, with NO_COLOR environment variable support
- Handles binary files, Unicode, and broken pipes robustly


## Requirements

- Python 3.6 or later
- No external dependencies


## Installation

### Linux, macOS

```bash
git clone https://github.com/rtulke/rp.git

# System-wide installation
cp rp/rp.py /usr/local/bin/rp
chmod +x /usr/local/bin/rp

# Or use a symlink
ln -s $(pwd)/rp/rp.py /usr/local/bin/rp
```


## Quick Start

```bash
# Highlight patterns in stdin
cat error.log | rp ERROR WARN INFO

# Search in a file
rp "exception" application.log

# Multiple patterns in a file
rp "error|ERROR" "warn|WARN" "info|INFO" system.log

# Recursive search in a directory
rp -r -i "todo|fixme" ~/projects/

# With line numbers and context
rp -n -C 3 "CRITICAL" system.log
```


## Usage

```
rp [OPTIONS] PATTERN [PATTERN ...] [FILE ...]
rp [OPTIONS] -e PATTERN [-e PATTERN ...] [FILE ...]
```

Patterns are regular expressions. Files and directories are specified after patterns. When no file arguments are given, rp reads from standard input.

Pattern and file arguments are split automatically: trailing arguments that exist on the filesystem are treated as files; the rest are patterns. Use `-e` to specify patterns explicitly when a pattern string might look like a file path.


## Options

### Pattern Specification

| Option | Description |
|--------|-------------|
| `-e PATTERN`, `--regexp PATTERN` | Explicit search pattern. Can be repeated. When `-e` is used, all positional arguments are treated as files. |
| `-f FILE`, `--file FILE` | Read patterns from FILE, one per line. Can be repeated to load from multiple files. |

### Match Behavior

| Option | Description |
|--------|-------------|
| `-i`, `--ignore-case` | Ignore case when matching patterns |
| `-v`, `--invert-match` | Print lines that do not match any pattern |
| `-w`, `--word-regexp` | Match only complete words (wraps patterns in `\b` boundaries) |
| `-k`, `--display-all` | Display all lines; only highlight matches instead of filtering |

### Output Control

| Option | Description |
|--------|-------------|
| `-n`, `--line-number` | Print line numbers before each output line |
| `-c`, `--count` | Print only the count of matching lines per file |
| `-o`, `--only-matching` | Print only the matched portion of each line |
| `-H`, `--with-filename` | Always print the filename prefix before each output line |
| `--no-filename` | Never print filename prefix, even when searching multiple files |
| `-Z`, `--null` | Separate filenames with a null byte instead of newline (for `-l`/`-L`; for use with `xargs -0`) |
| `-q`, `--quiet` | Suppress all output; exit 0 if any match is found, 1 otherwise |
| `-m NUM`, `--max-count NUM` | Stop after NUM matches per file. 0 means unlimited (default). |
| `--stats` | Print match statistics after output. Written to stderr. |
| `--color WHEN` | Control color output: `always`, `never`, or `auto` (default). Auto enables color only when stdout is a terminal and the `NO_COLOR` environment variable is not set. |

### Context

| Option | Description |
|--------|-------------|
| `-A NUM`, `--after-context NUM` | Print NUM lines after each match |
| `-B NUM`, `--before-context NUM` | Print NUM lines before each match |
| `-C NUM`, `--context NUM` | Print NUM lines before and after each match. Overrides `-A` and `-B`. |

Non-adjacent context groups are separated by `--` lines, matching the behavior of grep.

### File Selection

| Option | Description |
|--------|-------------|
| `-l`, `--files-with-matches` | Print only the names of files that contain at least one match |
| `-L`, `--files-without-match` | Print only the names of files that contain no matches |
| `-r`, `--recursive` | Search all files under each directory recursively. Hidden files and directories (names starting with `.`) are skipped. |
| `-I`, `--no-binary` | Skip binary files automatically |
| `--include GLOB` | Search only files whose names match GLOB. Can be repeated. Only applies during recursive search. Example: `--include="*.log"` |
| `--exclude GLOB` | Skip files whose names match GLOB. Can be repeated. Only applies during recursive search. |

### Miscellaneous

| Option | Description |
|--------|-------------|
| `--line-buffered` | Force line-buffered output. Useful when piping from `tail -f` or other streaming sources. |
| `-V`, `--version` | Print version and exit |


## Examples

### Basic Search

```bash
# Single pattern from stdin
cat app.log | rp "ERROR"

# Multiple patterns with different colors
cat app.log | rp "ERROR" "WARN" "INFO"

# Case-insensitive
cat app.log | rp -i "error" "warning"

# Show all lines, only highlight matches (no filtering)
cat config.txt | rp -k "TODO" "FIXME"
```

### Explicit Pattern Specification with -e

Use `-e` when a pattern might look like a filename, or when combining with multiple file arguments:

```bash
# Pattern that looks like a filename
rp -e "app.log" application.log

# Multiple explicit patterns
rp -e "ERROR" -e "WARN" app.log system.log

# Mix -e with -f
rp -e "CRITICAL" -f base-patterns.txt application.log
```

### Searching Files and Directories

```bash
# Single file
rp "pattern" file.log

# Multiple files
rp "error" app.log system.log access.log

# Recursive directory search
rp -r "TODO" ~/projects/

# Recursive, case-insensitive
rp -r -i "fixme" /var/log/

# Only .log files during recursion
rp -r --include="*.log" "ERROR" /var/log/

# Exclude compiled files during recursion
rp -r --exclude="*.pyc" --exclude="*.pyo" "pattern" src/

# Skip binary files
rp -r -I "search term" /usr/share/
```

### Regular Expressions

```bash
# IP addresses
cat access.log | rp "\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"

# Email addresses
cat dump.txt | rp "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# Timestamps
cat system.log | rp "\d{4}-\d{2}-\d{2}" "\d{2}:\d{2}:\d{2}"

# Multiple error variants
cat error.log | rp "err(or)?" "warn(ing)?" "exception"

# Whole words only
rp -w "test" file.txt
```

### Context Lines

```bash
# 3 lines after each match
rp -A 3 "ERROR" app.log

# 2 lines before each match
rp -B 2 "Exception" debug.log

# 3 lines before and after
rp -C 3 "CRITICAL" system.log

# Context with line numbers
rp -n -C 2 "error" application.log
```

### Output Modes

```bash
# Count matches per file
rp -c "error" *.log

# Count from multiple files
rp -c "warning" file1.log file2.log file3.log

# Only the matched text, not the whole line
rp -o "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}" access.log

# Lines that do not match
rp -v "DEBUG" application.log

# With line numbers
rp -n "error" app.log

# Stop after 5 matches
rp -m 5 "ERROR" large.log
```

### Filename Output

```bash
# List files containing matches
rp -l "ERROR" *.log

# List files with no matches
rp -L "ERROR" *.log

# Per-line filename prefix (grep style)
rp -H "ERROR" app.log system.log

# Filename prefix suppressed even for multiple files
rp --no-filename "ERROR" app.log system.log

# Null-separated filenames for xargs
rp -rlZ "ERROR" /var/log/ | xargs -0 vim
rp -rlZ "TODO" ~/projects/ | xargs -0 grep -l "FIXME"
```

### Quiet Mode for Shell Scripts

```bash
# Exit code only, no output
if rp -q "ERROR" app.log; then
    echo "Errors found"
fi

# Combined with recursive search
if rp -rq "password" ~/projects/; then
    echo "Potential credential leak found"
fi
```

### Statistics Mode

```bash
# Basic statistics
rp --stats "ERROR" "WARN" "INFO" application.log

# Output on stderr:
# === Statistics ===
# Total lines processed: 10000
# Lines with matches: 847
# Match rate: 8.47%
#
# Pattern matches:
#   ERROR: 42
#   WARN : 128
#   INFO : 677

# Statistics with count mode
rp --stats -c "error|exception" *.log

# Statistics on a recursive search
rp -r --include="*.log" --stats "ERROR" "WARN" /var/log/
```

### Pattern Files

```bash
# Load patterns from a file
rp -f patterns.txt access.log

# Multiple pattern files combined
rp -f security.txt -f network.txt system.log

# Pattern file with additional command-line patterns
rp -f patterns.txt "CRITICAL" system.log

# Pattern file with recursive search and statistics
rp -f security-patterns.txt --stats -r /var/log/
```

### Real-time Log Monitoring

```bash
# Monitor a log file in real-time
tail -f app.log | rp "ERROR" "EXCEPTION" "CRITICAL"

# With line-buffered output to ensure no delay
tail -f app.log | rp --line-buffered "ERROR" "WARN"
```

### Color Control

```bash
# Force color even when piping (e.g. into less -R)
rp --color=always "ERROR" app.log | less -R

# No color output
rp --color=never "ERROR" app.log > report.txt

# Disable color via environment variable
NO_COLOR=1 rp "ERROR" app.log
```

### Combining Tools

```bash
# With find
find . -name "*.log" -exec rp "ERROR" {} +

# With xargs
cat file-list.txt | xargs rp "pattern"

# With awk
cat data.txt | awk '{print $3}' | rp "pattern"

# Full log analysis
rp -r --include="*.log" -f patterns.txt --stats -n -C 2 -i /var/log/

# Find files with errors and open them
rp -rlZ "Exception" src/ | xargs -0 vim

# Security audit
rp -r -I --stats -f security-patterns.txt /var/log/ 2>/dev/null

# Find potential credential leaks in source
rp -r -i "password|secret|api_key|token" --stats src/
```


## Pattern File Format

Pattern files contain one regular expression per line. Empty lines and lines starting with `#` are ignored.

```text
# HTTP error status codes
\b[45]\d{2}\b

# Common log levels
ERROR
WARNING
CRITICAL

# IP addresses
\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b

# Authentication failures
authentication.*failed
permission.*denied
```

Usage:

```bash
rp -f patterns.txt access.log
```


## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | At least one match was found |
| 1 | No matches found |
| 2 | Error occurred (invalid pattern, file not found, etc.) |
| 130 | Interrupted by Ctrl+C |
| 141 | Broken pipe |


## Performance

rp processes each file in a single pass. All patterns are pre-compiled before scanning begins. For multi-pattern searches this avoids the overhead of running multiple grep invocations.

Benchmarks (1 million lines, 4 patterns):

```
grep (4 separate calls): approx. 3.5s
rp v3 (grep-based, multiple passes): approx. 4.2s
rp v5 (Python, single pass): approx. 1.8s
```

For single-pattern searches without colorization, grep remains faster due to native C implementation and SIMD optimizations. rp's advantage is multi-pattern search, color output, and statistics in one pass.


## Contributing

Contributions are welcome. Please keep the tool as a single file and ensure any changes are tested against the documented examples. Code should follow PEP 8 style.
