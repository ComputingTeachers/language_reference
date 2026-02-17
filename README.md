Language Reference
==================

* Programming language reference for multiple languages
* For each language: Examples of: variables, iteration, if-statements, functions, open-file, split-strings, etc
* Select one language, or multiple languages (to compare)
* Printable


Rational
--------

### Teaching Aid

* At the foundation level, most languages can perform arithmetic, print to the screen and loop over a sequence. When used at the high levels, languages can be very different, but most of those concepts/patterns/advanced-features are not understandable/relevant to beginners.
* From the beginning, Learners don't identify as knowing one language. They understand that the foundation concepts apply across multiple languages. This encourages them to identify as a 'programmer' rather than just a 'python programmer'.
* With language_reference the learners can be supported in moving between languages freely.
* Lesson can be delivered in different languages.
* Advanced learners can use language_reference to tackle a task in a different language to the rest of a class
* 1 sheet A4 (duplexed) split into 4 columns for 4 languages. One sheet is not overwhelming. It can be given at the start of a course and be a familiar recurring aid. Saying "Just one column of this sheet is all the core programming constructs you need for the exam" gives a finite visual representation. Students can measure there progress on how much of the column they understand.

### Professional reference

* Keeping the exact syntax of 5 languages in your head at once over years can be tricky. The sheet can be used a quick lookup/refresher.


History
-------

* 2008: Created a resource for teaching A-Level Computing and demoed it at the first ComputingAtSchool conference in 2009
* 2012: Started the `TeachProgramming` repo with a custom version builder to split small code projects into diff chunks for learners to incrementally build mini projects.
    * [LanguageCheetSheet.odt](https://github.com/calaldees/TeachProgramming/commits/4d152d58d2c321c5867f267d7a4e62d56b950711/teachprogramming/static/docs/LanguageCheetSheet.odt?browsing_rename_history=true&new_path=teachprogramming/static/docs/LanguageCheetSheet%20[deprecated].odt&original_branch=master) an early versions of an OpenOffice document
* 2021: Created [dynamic html language renderer](https://github.com/ComputingTeachers/language_reference/commits/main/static/langauge_reference.html)
* 2026: Moved language_reference to it's own repository


Tools (in this repo)
=====

* `make_ver`
    * A tool to break a single source file into multiple versions.
    * Versions are marked by the comment at the end of a line with `VER: name`
* `static`
    * Dynamic html/js renderers for the data derived from `make_ver`
* `verify_snippets` (for projects)
    * Automated test suite for incremental versions.
    * Run tests to assert that each project version outputted compiles (and maybe runs).


Example Versions
----------------

### `language_reference`

* Uses version by having a single source file for a language and marking each line with version name
* Examples
    * [python.py](./language_reference/languages/python/python.py)
    * [Java.java](./language_reference/languages/java/Java.java)


```python
a = 1           # VER: arithmetic
print('hello')  # VER: output
```

### `projects`

* Uses versions by having a sequence of versions to build-up a complete solution incrementally
* Example
    * [copter.ver.json](https://github.com/calaldees/TeachProgramming/blob/master/teachprogramming/static/projects/game/copter.ver.json)
    * [copter.html](https://github.com/calaldees/TeachProgramming/blob/master/teachprogramming/static/projects/game/copter.html)
    * [copter.py](https://github.com/calaldees/TeachProgramming/blob/master/teachprogramming/static/projects/game/copter.py)


Projects
========

Because projects are bigger and could contain further assets, projects are typically stored in another repo.
`make_ver` and 'html/js project renderer' are stored in this repo because the functionality is built on the foundations that are used in generating `language_reference` versions and renderer.

* A folder is recursively crawled for all `.ver` files.
* For each `NAME.ver` file, all the languages that are loaded e.g. `NAME.py`+`NAME.java`+`NAME.cs`
* A set of diff's are made for each version name incrementally
* A html/js viewer renders the diffs for each language


`verify_snippets` (for projects)
-----------------

