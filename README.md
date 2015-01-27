Ipynb-viewer
============

Rendering local ipynb to static HTML

About
=====

this is a project from make your ipynb file to html without serve by ipython notebook. why do this?


* Usually I only need the other people see my data result, the other people no need to modify or execute it


* I often generate many such ipynb files, but I need to use `nbconvert `transformation every time

so. Ipynb-viewer can do this:

* use a simple web service instead of ipython botebook's service
* support show ipynb files like ipython notebook tree(/tree)
* custom port and template simple and easy

Install and Usage
=====

You can install from pip:

    pip install ipynbviewer

start it:

	cd /the/notebook/files/path
	python -m ipynbviewer # http://localhost:8000 and use ipython built-in template: full.tpl

or:

    python -m ipynbviewer -p 54001 # http://localhost:54001

or:

    python -m ipynbviewer -p 54001 -t double11.tpl # http://localhost:54001 and use custom template named `double11.tpl` in current dir.
