rpen
====

rpen - red pencil, is a simple multicolor comandline text high lighter.

![Example](/images/rpen1.png)


Requirements
------------

* Python 2.5 or higher
* egrep or grep 

Installation
------------

```bash
git clone https://github.com/rtulke/rpen.git
cp rpen/rpen.py /usr/local/bin/rpen
chmod 777 /usr/local/bin/rpen (systemwide)
```

Usage
-----

```
$ rpen
Usage: cat logfile | rpen [options] searchterm1 searchterm2...

Options:
  -h, --help  show this help message and exit
  -i          perform a case insensitive search
  -k          only highlight, do not filter
 ````

Examples
--------

```bash
cat /foo/bar | rpen searchstring1 searchstring2 .. 
```

or try less with RAW mode:

```bash
cat /foo/bar | rpen searchstring1 searchstring2 .. | less -R 
```

rpen with regex:

```bash
cat /foo/bar | rpen ^.*[04]
```

highlight whole line:

```bash
cat /foo/bar | rpen ^.\*searchstring\*.$
```

```bash
cat /foo/bar | rpen -i Searchstring1 searchString2 .. | less -R 
```
