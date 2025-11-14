---
trigger: model_decision
description: This standard should be applied to all Python code.
globs: 
---

# Python Coding Style 2025

## Google Python Style Guide

The [Google Python Style Guide][GPSG] (GPSG) contains a lot of good advice. I choose to follow most of their 
suggestions, with some notable exceptions:

- Always follow [Black]/[Ruff] formatting (see below). 
- Use imperative voice for docstrings (Yes: "Fetch rows from database."; No: "Fetches rows from the database.")
- If the linters (as configured below) contradict Google's style, go with the linter.
- Use of `@staticmethod` is fine for private helper methods that do not need to read or write the object's state.

## Imports

Follow the [GPSG] for imports.

### datetime

The datetime library is kind of a snowflake in that `datetime.date`, `datetime.datetime`, `datetime.time`,  and 
`datetime.timedelta` are classes (despite the lower case). Do not import the classes directly; instead always import 
the library as `dt` --  because it's short and avoids confusion with the class of the same name.

```python
import datetime as dt

dt.datetime()
```

## Code Formatting

All code follows the [PEP-8] standard and is formatted with the [Black]/[Ruff] code formatter. Type hinting tends to add a lot to the length of code lines, so we make an exception to [PEP-8] and set the max line length to 120 characters.

Code format should pass [Ruff] checks. 

Imports should be organized according to the [PEP-8] standard and can be maintained using [Ruff].

[Ruff], any [mypy] can all be configured by creating a `pyproject.toml` file in the root of the project 
(see \[pyproject.toml\](https://bitbucket.org/toadstule/workspace/snippets/5kkdX5/pyprojectoml)).

### Code Comments

Public comments are made with docstrings, following the [PEP-257] standard, using the [Google Style. Code][GPSG] 
comments should pass [Ruff] checks.

### Class Variables

To avoid confusion, it is preferred to reference class variables by their class name, for example `Shape.width`, 
rather than using `self.__class__.width` (less readable) or `self.width` (dangerous). The exception to this is when 
the class variables are type-hinted as `Final`; in this case the `self` reference may be used (`self.width`).

### Type Hints

Using type hints is recommended and can reduce errors that are often only caught at runtime. Type hinting is defined 
in [PEP-484] and continues to evolve with new Python releases. Type-hinted (and  non-type-hinted) code should pass 
[pytype] and/or [mypy] checks.

### Code Layout

#### Class Layout

Classes should be laid out following as follows:

- public data (alphabetical)
- private data (alphabetical)
- `__init__` constructor
- other dunder methods (alphabetical)
- public:
  - class methods (alphabetical)
  - properties (alphabetical)
  - methods(alphabetical)
  - static methods (alphabetical) -- these should almost never exist
- private:
  - class methods (alphabetical)
  - properties (alphabetical)
  - methods(alphabetical)
  - static methods (alphabetical)

#### File Layout

Again following the [PEP-8] standard with this general layout:

- shebang (only if this file is supposed to be run directly)
- file docstring
- imports
- global variables
- public classes (alphabetical)
- public functions (alphabetical)
- private classes (alphabetical)
- private functions (alphabetical)
- `__main__` section

## Python Projects and Layout

(See [[Python Projects|Coding/Python/Python Projects.md]] for more information.)

## Miscellaneous Topics

### Argument Parsing

Some style guidelines for using `arg_parse`:

- `help=` -- should be a sentence fragment with no initial capital or ending punctuation.
- `description=` -- Full sentence(s), with capital letter and ending punctuation.

### Project Version Management

The project version source of truth is the `pyproject.toml` file. Having the project
reference this value at runtime can be accomplished by putting this in the project's
`__init__.py` file:

```python
import importlib.metadata

__version__ = importlib.metadata.version("my_project")
```

<!-- Links -->
[Black]: https://pypi.org/project/black/
[GPSG]: https://google.github.io/styleguide/pyguide.html
[isort]: https://pypi.org/project/isort/
[mypy]: http://mypy-lang.org/
[PEP-8]: https://www.python.org/dev/peps/pep-0008/
[PEP-257]: https://www.python.org/dev/peps/pep-0257/
[PEP-484]: https://www.python.org/dev/peps/pep-0484/
[pydocstyle]: https://pypi.org/project/pydocstyle/
[Pylint]: https://www.pylint.org/
[pytype]: https://github.com/google/pytype/
[Ruff]: https://docs.astral.sh/ruff/
