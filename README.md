rpen
====

rpen (Red Pencil) is a comandline text highlighter based on egrep

Requirements:
-------------

* Python 2.5 or higher
* egrep or grep 

Installation:
-------------
* download rpen
* mv rpen.py rpen
* cp rpen /usr/local/bin/
* chmod 777 /usr/local/bin/rpen (systemwide)

Examples:
---------
<code>
$ cat /foo/bar | rpen searchstring1 searchstring2 .. 
</code>


or try less with RAW mode

<code>
$ cat /foo/bar | rpen searchstring1 searchstring2 .. | less -R 
</code>


rpen with regex:

<code>
$ cat /foo/bar | rpen ^.*[04]
</code>


highlight whole line:

<code>
$ cat /foo/bar | rpen ^.\*searchstring\*.$
</code>


if first arg i --> case_insensitive:

<code>
$ cat /foo/bar | rpen -i Searchstring1 searchString2 .. | less -R 
</code>

