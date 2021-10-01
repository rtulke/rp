rpen
====

rpen - red pencil, is a simple multicolor comandline text highlighter.

I always had problems with filtering out large continuous text, i.e. text that you want to filter out of log files with cat or something like that. So I needed a tool with which I can easily recognize what I'm actually looking for. 


![Example](/images/rpen1.png)


Requirements
------------

* Python 2.5x, 2.7x or Python 3.x
* commandline tool: egrep or grep 

Setup
-----

```bash
git clone https://github.com/rtulke/rpen.git
cp rpen/rpen.py /usr/local/bin/rpen
chmod 777 /usr/local/bin/rpen
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
