rp
==

rp - red pencil is a simple multicolor command-line tool to highlight the filtered output text with multi-pattern highlighting, regex support, and advanced statistics. Each search pattern gets its own color, making it easy to visually distinguish multiple patterns in log files and text output.

I always had problems with filtering out large continuous text, i.e. text that you want to filter out of log files with cat or something similar. So I needed a tool that makes it easy to see what I'm actually looking for.

![Example](/images/rpen1.png)


## Features

- **Multi-color highlighting** - Each pattern gets a unique color
- **Full regex support** - Use powerful regular expressions
- **Statistics mode** - Get detailed match counts per pattern
- **File and directory support** - Search single files or recursively
- **Context lines** - Show lines before/after matches (like `grep -A/-B/-C`)
- **Multiple output modes** - Count, only-matching, invert, and more
- **Performance optimized** - Single-pass processing
- **Robust** - Handles binary files, unicode, broken pipes

## Requirements

* Python 3.6
* egrep or grep, grep should be GNU Version 3.x

## Installation Linux

```bash
# clone repository
git clone https://github.com/rtulke/rp.git

# for system wide installation
cp rp/rp.py /usr/local/bin/rp
chmod +x /usr/local/bin/rp

# or optinal use symlink insted of copy to /usr/local/bin
# ln -s $(pwd)/rp.py /usr/local/bin
```

## Installation MacOS

Mac OS X uses BSD grep or egrep, which are not 100% compatible with Linux grep/egrep. Most functions should work. If you encounter any problems, please create an issue.

## Quick Start

```bash
# Basic usage with stdin
cat error.log | rp ERROR WARN INFO

# Search in files
rp "exception" application.log

# Multiple patterns with colors
rp "error|ERROR" "warn|WARN" "info|INFO" system.log

# Recursive directory search
rp -r -i "todo|fixme|hack" ~/projects/

# With line numbers and context
rp -n -C 3 "CRITICAL" system.log
```

## Usage

```
rp [OPTIONS] PATTERN [PATTERN...] [FILE...]
```

### Basic Options

| Option | Description |
|--------|-------------|
| `-i, --ignore-case` | Ignore case distinctions in patterns |
| `-k, --display-all` | Display all lines, only highlight matches |
| `-v, --invert-match` | Select non-matching lines |
| `-w, --word-regexp` | Match only whole words |

### Output Control

| Option | Description |
|--------|-------------|
| `-n, --line-number` | Print line numbers with output |
| `-c, --count` | Print only count of matching lines |
| `-o, --only-matching` | Print only matched parts of lines |
| `--stats` | Display detailed statistics about matches |

### Context Control

| Option | Description |
|--------|-------------|
| `-A NUM, --after-context NUM` | Print NUM lines after match |
| `-B NUM, --before-context NUM` | Print NUM lines before match |
| `-C NUM, --context NUM` | Print NUM lines before and after match |

### File Handling

| Option | Description |
|--------|-------------|
| `-r, --recursive` | Search directories recursively |
| `-I, --no-binary` | Skip binary files automatically |
| `-f FILE, --file FILE` | Read patterns from FILE (one per line) |

## Examples

### Basic Searching

```bash
# Single pattern
cat app.log | rp "ERROR"

# Multiple patterns with different colors
cat app.log | rp "ERROR" "WARN" "INFO"

# Case-insensitive search
cat app.log | rp -i "error" "warning"

# Show all lines, only highlight
cat config.txt | rp -k "TODO" "FIXME"
```

### Regex Patterns

```bash
# IP addresses
cat access.log | rp "\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"

# Email addresses
cat dump.txt | rp "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# Timestamps
cat system.log | rp "\d{4}-\d{2}-\d{2}" "\d{2}:\d{2}:\d{2}"

# Multiple error types
cat error.log | rp "err(or)?" "warn(ing)?" "exception"
```

### File Operations

```bash
# Single file
rp "pattern" file.log

# Multiple files
rp "error" *.log

# Recursive directory search
rp -r "TODO" ~/projects/

# Recursive with case-insensitive
rp -r -i "fixme" /var/log/

# Skip binary files
rp -r -I "search term" /usr/share/
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
# Count matches only
rp -c "error" *.log

# Count per file
rp -c "warning" file1.log file2.log file3.log

# Show only matching parts
rp -o "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}" access.log

# Invert match (exclude lines)
rp -v "DEBUG" application.log

# Line numbers
rp -n "error" app.log
```

### Statistics Mode

```bash
# Basic statistics
rp --stats "ERROR" "WARN" "INFO" application.log

# Output:
# [... colored matches ...]
#
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

# Statistics without match output
rp --stats -c "pattern" large.log
```

### Pattern Files

Create a pattern file (`patterns.txt`):

```text
# Security-related patterns
authentication.*failed
permission.*denied
unauthorized.*access

# Error patterns
\b(error|exception|fatal)\b

# Network patterns
\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}
```

Use the pattern file:

```bash
# From file only
rp -f patterns.txt access.log

# Combine file and command-line patterns
rp -f patterns.txt "CRITICAL" system.log

# With statistics
rp -f security-patterns.txt --stats -r /var/log/

# Recursive with pattern file
rp -f patterns.txt -r -I ~/logs/
```

### Advanced Combinations

```bash
# Full log analysis
rp -f patterns.txt --stats -n -C 2 -i -r /var/log/

# Security audit
rp -f security-patterns.txt -r -I --stats /var/log/ 2>/dev/null

# Development workflow
rp -r -i "TODO|FIXME|HACK|XXX" --stats ~/project/src/

# Monitor logs in real-time
tail -f app.log | rp "ERROR" "EXCEPTION" "CRITICAL"

# Find specific issues with context
rp -n -C 5 "OutOfMemory|StackOverflow" *.log
```

## Pattern File Format

Pattern files support:
- One pattern per line
- Comments starting with `#`
- Empty lines (ignored)
- Full regex syntax

Example (`patterns.txt`):
```text
# HTTP status codes
\b[45]\d{2}\b

# Common log levels
ERROR
WARNING
CRITICAL

# IP addresses
\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Matches found |
| 1 | No matches found |
| 2 | Error occurred |
| 130 | Interrupted (Ctrl+C) |
| 141 | Broken pipe |

## Performance

**Optimizations:**
- Single-pass processing (no repeated pipe overhead like v3)
- Pre-compiled regex patterns
- Efficient context buffer with deque
- Lazy file iteration
- Binary file detection (first 8KB)

**Benchmarks** (1M lines, 4 patterns):
```
grep (4 calls): ~3.5s
rp v3:         ~4.2s (grep-based, multiple passes)
rp v5:         ~1.8s (Python, single pass)
```

## Comparison with grep

| Feature | grep | rp |
|---------|------|-----|
| Multi-color highlighting | ❌ | ✅ |
| Regex support | ✅ | ✅ |
| Context lines | ✅ | ✅ |
| Statistics | ❌ | ✅ |
| Pattern files | ✅ | ✅ |
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Single pattern | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Multiple patterns | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Use Cases

### Security Analysis
```bash
rp -f security-patterns.txt --stats -r /var/log/
```

### Development
```bash
rp -r "TODO|FIXME|HACK" --stats src/
```

### Log Monitoring
```bash
tail -f app.log | rp "ERROR" "WARN" "EXCEPTION"
```

### Incident Response
```bash
rp -n -C 5 "OutOfMemory|Segfault|Panic" *.log
```

### Code Review
```bash
rp -r -i "password|secret|key|token" --stats .
```

## Tips & Tricks

### Color Output in Less
```bash
rp "pattern" file.log | less -R
```

### Save Colored Output
```bash
rp "pattern" file.log > output.txt  # No colors
script -c 'rp "pattern" file.log' output.txt  # With colors
```

### Combine with Other Tools
```bash
# With find
find . -name "*.log" -exec rp "ERROR" {} +

# With xargs
cat file-list.txt | xargs rp "pattern"

# With awk
cat data.txt | awk '{print $3}' | rp "pattern"
```

### Word Boundaries
```bash
# Match "test" but not "testing"
rp -w "test" file.txt

# Multiple whole words
rp -w "error" "warning" "info" log.txt
```

## Troubleshooting

### Binary File Warnings
```bash
# Skip binary files automatically
rp -I "pattern" /path/

# Or redirect stderr
rp "pattern" /path/ 2>/dev/null
```

### Performance Issues
```bash
# Use simpler patterns when possible
rp "ERROR" instead of "E[RR]*O[RR]*"

# Limit recursion depth (use find)
find /path -maxdepth 2 -name "*.log" -exec rp "pattern" {} +
```

### Unicode Issues
Unicode is handled with `errors='replace'` - invalid sequences are replaced with �

## Contributing

Contributions welcome! Please ensure:
- Code follows PEP 8
- All features have examples
- Error handling is robust
- Performance is tested
- One single file ;)
