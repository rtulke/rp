rp
==

rp - red pencil, is a simple multicolor command-line tool to filter and highlight the output text. 

I always had problems with filtering out large continuous text, i.e. text that you want to filter out of log files with cat or something similar. So I needed a tool that makes it easy to see what I'm actually looking for.

![Example](/images/rpen1.png)


Requirements
------------

* Python 2.5x, 2.7x or Python 3.x
* egrep or grep, grep should be GNU Version 3.x

Setup Linux
-----------

```bash
git clone https://github.com/rtulke/rp.git
cp rp/rp.py /usr/local/bin/rp
chmod 777 /usr/local/bin/rp
```

Setup MacOS X
-------------

Mac OS X uses the BSD grep or egrep which is not 100% compatible with Linux grep/egrep. Therefore it requires an additional -e "OK" which must be used directly in the code.

Otherwise you will get this error message: "egrep: empty (sub)expression"


Usage
-----

```
$ rp
Usage: cat logfile | rp [options] searchterm1 searchterm2...

Options:
  -h, --help  show this help message and exit
  -i          perform a case insensitive search
  -k          only highlight, do not filter
 ````

Examples
--------

```bash
cat /foo/bar | rp searchstring1 searchstring2 .. 
```

or try less with RAW mode:

```bash
cat /foo/bar | rp searchstring1 searchstring2 .. | less -R 
```

rp with regex:

```bash
cat /foo/bar | rp ^.*[04]
```

highlight whole line:

```bash
cat /foo/bar | rp ^.\*searchstring\*.$
```

```bash
cat /foo/bar | rp -i Searchstring1 searchString2 .. | less -R 
```
