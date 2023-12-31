git_hooks
=========

This repository contains a CMake file which generates a git hook that can format and check your source files before you commit them to your repository.

Setup
-----

0. Install the formatters and linters for the file types that you want to format/lint (by default, it is enabled only for C/C++, so only these are mandatory):
 - C/C++: Install clangd and clang-format
 - CMake: `pip install --user cmake_format`
 - Python: `sudo apt install python-autopep8 pylint`
1. Ensure that `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` is included in the CMake arguments when using CMake and formatting/linting C++ code.
2. If you use `aduulm_cmake_tooks`, you can include the git hooks in any of your packages' toplevel `CMakeList.txt` with a call to `setup_git_hooks()`. Otherwise, you may add the git_hooks repository as a submodule of your own repository and then include it with `add_subdirectory("git_hooks")` and `setup_git_hooks()`
3. Build your CMake project
4. Check that `./run_hooks` and `$(git rev-parse --git-dir)/hooks/pre-commit` exist
5. Add `run_hooks` to your .gitignore file
6. Change some C++ files and see that they are formatted and checked when you commit the changes.

Format all files
----------------

The pre-commit hook and the run_hooks script only check and format **staged** files by default. If you want to run it on all files in the repository at once, run `./run_hooks --all`

Only run formatter or linter
---------------------------------

 - Formatter: `./run_hooks --all --modes format`
 - Linter: `./run_hooks --all --modes lint`
 - Both: `./run_hooks --all --modes format,lint` or just `./run_hooks --all`

Auto-fix linting errors
-----------------------

To fix linter errors, run `./run_hooks --all --fix`

Temporarily disable linting
---------------------------

If you want to make an intermediate commit and your source code does not compile yet, you can disable linting temporarily by setting the environment variable `LINT` to `0`, e.g.:

```sh
DISABLE_LINTING=1 git commit -m ...
```

or

```sh
export DISABLE_LINTING=1
...
git commit -m ...
git commit -m ...
...
unset DISABLE_LINTING
```

Configuration
-------------

You can pass arguments to the `setup_git_hooks` or `create_git_hook` call (`setup_git_hooks` is just a wrapper for `create_git_hook`, so they take the same arguments):
```cmake
# Abort commit when files need formatting
setup_git_hooks(ABORT_COMMIT)

# defines which tools should be run on pre-commit (comma-separated list of: format, lint)
setup_git_hooks(MODES "format")

# colon-separated list of directories to ignore
setup_git_hooks(IGNORE_DIRS "src:include")

# Style option for clang-format (-style=...)
# You should probably leave this at "file", so that it uses
# the .clang-format file from the sandbox root
setup_git_hooks(CLANG_FORMAT_STYLE "file")

# comma-separated list of clang-tidy checks to perform
setup_git_hooks(CLANG_TIDY_CHECKS "readability-*,bugprone-*,modernize-*,google-*")

# You can set the formatters that should be run for all supported file types.
# Here are the defaults:
setup_git_hooks(cpp_FORMATTERS "clang-format") # Allowed: clang-format
setup_git_hooks(cpp_LINTERS "clang-tidy") # Allowed: clang-tidy
setup_git_hooks(cmake_FORMATTERS "") # Allowed: cmake-format
setup_git_hooks(cmake_LINTERS "")
setup_git_hooks(py_FORMATTERS "") # Allowed: autopep8
setup_git_hooks(py_LINTERS "") # Allowed: pylint
```

You may only have one call to `setup_git_hooks()` per package/project. You can however specify multiple options in one call. Remember to re-build your package after changing the `CMakeLists.txt`. There also exist global variants of the above options (except for `IGNORE_DIRS`) under the `GCF_GLOBAL_` prefix.

 - `GCF_GLOBAL_ABORT_COMMIT`: Same as `ABORT_COMMIT`, but for all projects
 - `GCF_GLOBAL_MODES`: Same as `MODES`, but for all projects
 - `GCF_GLOBAL_CLANG_FORMAT_STYLE`: Same as `CLANG_FORMAT_STYLE`, but for all projects
 - `GCF_GLOBAL_CLANG_TIDY_CHECKS`: Same as `CLANG_TIDY_CHECKS`, but for all projects
 - `GCF_GLOBAL_py_LINTERS`: Same as `py_linters`, but for all projects

Disable a warning for a single line of code
-------------------------------------------

In case of false positives, you can use a `// NOLINT` comment to signalize to `clang-tidy` that the line does not contain errors. Example:

```c
return true; // NOLINT

// or

// NOLINTNEXTLINE
return true;
```

Usage in Projects without CMake
-------------------------------

If your project does not use CMake (e.g. pure Python projects), but want to use a git hook for auto-formatting, you can use the `init.sh` script to create a minimal CMakeLists.txt file and a shell script for you, which can be used to configure the git hooks. Example:

```sh
/path/to/aduulm_sandbox/root/git_hooks/init.sh /path/to/project
# Creates CMakeLists.txt and configure_hooks.sh in git root of project
```
Then adapt CMakeLists.txt e.g. by changing the call to `create_git_hook()` to `create_git_hook(py_FORMATTERS "autopep8")`. Then, run `./configure_hooks.sh`, which will create/update the hooks.

Caveat
------

Because `clang-tidy` can only infer compiler flags for C++ source files and not for header files, header files which are not included by any source file in your project can not be checked. `#include` your header files in a source file if you want them to be checked (or use something like [compdb](https://github.com/Sarcasm/compdb)).

Problems
--------

If the git hooks produce errors about not finding header files and the following:

```
 Could not auto-detect compilation database from directory "/home/user/aduulm_sandbox/build/package_name"
 No compilation database found in /home/user/aduulm_sandbox/build/package_name or any parent directory
 fixed-compilation-database: Error while opening fixed database: No such file or directory
 json-compilation-database: Error while opening JSON database: No such file or directory
```

This means that it can not find the compilation database, which contains the flags which are needed to compile your files. This can occur in 2 cases:

 * You did not build your CMake project before committing or the flags changed since you last built your backage.
 * The path to your CMake project has changed. To fix this, navigate to the root of your workspace and delete all files generated by the git hooks:
  ```bash
  find . -name ".git" -type d | xargs -n1 -I _DIR_ find _DIR_ -name "*.config.yaml" -exec rm {} \;
  find . -name ".git" -type d | xargs -n1 -I _DIR_ find _DIR_ -name "pre-commit" -exec rm {} \;
  find . -name "run_hooks" -exec rm {} \;
  ```
Then build your project again (which will cause the git hooks to re-create the necessary files) and try to commit again.

Source
------

Based on https://github.com/kbenzie/git-cmake-format

License
=======

License: Apache 2.0

Authors: Jan Strohbeck (MRM)

Maintainers: Jan Strohbeck, Thomas Wodtko, Robin Dehler, Michael Kösel (MRM)

Affiliation: Institute of Measurement, Control and Microtechnology (MRM), Ulm University
