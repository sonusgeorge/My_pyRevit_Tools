# -*- coding: UTF-8 -*-
"""SG-Tools shared library.

Anything in this folder can be imported by ANY script in this extension,
because pyRevit automatically adds `<extension>/lib` to the Python path.

Example, from inside any script.py:

    from sg.naming import natural_sort_key

Rule of thumb: if you write the same code in a second tool, move it here.
Do not move code here "just in case" -- only after it is used twice.
"""
