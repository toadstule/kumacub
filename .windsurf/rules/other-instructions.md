---
trigger: always_on
description: 
globs: 
---

Unit tests can be run with: `make test`.

Formatting, linting and unit tests can be run with `make format check`.

Don't get into a loop of fixing `ruff` linter errors. If you get into a state where there are a lot of linter errors, just verify that the tests pass (`make test`) and I will deal with the linter errors.

Prefer importing of modules, rather than importing functions or classes:

  - Bad: `from pathlib import Path`
  - Good: `import pathlib`


