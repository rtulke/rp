rpen
====

rpen is a text highlighter based on egrep

try:

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
