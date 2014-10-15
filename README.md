rpen
====

rpen is a text highlighter based on egrep

try:

<code>
$ cat /foo/bar | rpen searchstring1 searchstring2 .. 
</code>>

or try
<code>
$ cat /foo/bar | rpen searchstring1 searchstring2 .. | less -R 
</code>

for regex
<code>
$ cat /foo/bar | rpen ^.*[04]
</code>
