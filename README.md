rpen
====

rpen (Red Pencil) is a comandline text highlighter based on egrep

Requirements:
-------------

* Python 2.5 or higher
* egrep or grep 

Installation:
-------------
* download rpen.py or use git:

```bash
git clone https://github.com/rtulke/rpen.git
cp rpen/rpen.py /usr/local/bin/rpen
chmod 777 /usr/local/bin/rpen (systemwide)
```


Examples:
---------
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

if first arg i --> case_insensitive:

```bash
cat /foo/bar | rpen i Searchstring1 searchString2 .. | less -R 
```
