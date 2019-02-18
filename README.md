README
======

This repository contains a CMake file which generates a git hook that can format and check your source files before you commit them to your repository.

Setup
-----

0. Install the formatters and linters for the file types that you want to format/lint (by default, it is enabled only for C/C++, so only these are mandatory):
 - C/C++: `sudo apt install clang-format-6.0 clang-tidy-6.0`
 - CMake: `pip install --user cmake_format`
 - Python: `pip install --user python-autopep8 pylint`
1. Ensure that `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` is included in the `cmake_args` of your catkin profile. It is already added to the default profile, but if you have created your own catkin profile, you need to add the flag with `catkin config -a --cmake-args "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"`)
2. If you use `aduulm_cmake_tooks`, you can include the git hooks in any of your packages' toplevel `CMakeList.txt` with a call to `setup_git_hooks()`. Otherwise, you may add the following code block explicitly (not recommended):
```cmake
set(HOOKS_PATH "${CMAKE_BINARY_DIR}/../../root/git_hooks")
if(EXISTS "${HOOKS_PATH}")
  add_subdirectory("${HOOKS_PATH}" "${CMAKE_CURRENT_BINARY_DIR}/.hooks")
  create_git_hook()
else()
  message(WARNING "Could not find git hooks. Git hooks are not active.")
endif()
```
3. Run `catkin build` or `catkin build PROJECT_NAME`
4. Check that `./run_hooks` and `$(git rev-parse --git-dir)/hooks/pre-commit` exist
5. Add `run_hooks` to your .gitignore file
6. Change some C++ files and see that they are formatted and checked when you commit the changes.

Format all files
----------------

The pre-commit hook only checks and formats changed files. If you want to run it on all files in the repository at once, run `./run_hooks --all`

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
LINT=0 git commit -m ...
```

or

```sh
export LINT=0
...
git commit -m ...
git commit -m ...
...
unset LINT
```

Configuration
-------------

You can pass arguments to the `setup_git_hooks` or `create_git_hook` call (`setup_git_hooks` is just a wrapper for `create_git_hook`, so they take the same arguments):
```cmake
# Abort commit when files need formatting
setup_git_hooks(ABORT_COMMIT)

# defines which tools should be run on pre-commit (comma-separated list of: format, tidy)
setup_git_hooks(MODES "format")

# comma-separated list of directories to ignore
setup_git_hooks(IGNORE_DIRS "src,include")

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

You can specify multiple options in one call. Remember to re-build your package after changing the `CMakeLists.txt`. There also exist global variants of the above options (except for `IGNORE_DIRS`) under the `GCF_GLOBAL_` prefix, which you can set e.g. in your Catkin profile:

 - `GCF_GLOBAL_ABORT_COMMIT`: Same as `ABORT_COMMIT`, but for all projects
 - `GCF_GLOBAL_MODES`: Same as `MODES`, but for all projects
 - `GCF_GLOBAL_CLANG_FORMAT_STYLE`: Same as `CLANG_FORMAT_STYLE`, but for all projects
 - `GCF_GLOBAL_CLANG_TIDY_CHECKS`: Same as `CLANG_TIDY_CHECKS`, but for all projects
 - `GCF_GLOBAL_py_LINTERS`: Same as `py_linters`, but for all projects

Example in Catkin profile `config.yaml`:

```yaml
cmake_args:
- -DGCF_GLOBAL_ABORT_COMMIT=TRUE
- -DGCF_GLOBAL_MODES=format
```

Note that when you change your catkin config, you need to clean the workspace and re-build your packages.

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

 * You did not build your package before committing or the flags changed since you last built your backage. Build your package with `catkin build package_name`.
 * Your package was moved or renamed. To fix this, navigate to the root of your catkin workspace and delete all files generated by the git hooks:
  ```bash
  find src -name "run_hooks" -exec rm {} \;
  find .git -name "*.config.yaml" -exec rm {} \;
  find .git -name "pre-commit" -exec rm {} \;
  ```
  Then build your package (which will cause the git hooks to re-create the necessary files) and try to commit again.

Source
------

Based on https://github.com/kbenzie/git-cmake-format
