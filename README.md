rpen
====

rpen is a text highlighter based on egrep

try:

<syntaxhighlight lang="bash">
$ cat /foo/bar | rpen searchstring1 searchstring2 .. 
</syntaxhighlight>

or try
<syntaxhighlight lang="bash">
$ cat /foo/bar | rpen searchstring1 searchstring2 .. | less -R 
</syntaxhighlight>

for regex
<syntaxhighlight lang="bash">
$ cat /foo/bar | rpen ^.*[04]
</syntaxhighlight>
