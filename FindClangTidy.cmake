#
#.rst:
# FindClangTidy
# ---------------
#
# The module defines the following variables
#
# ``CLANG_TIDY_EXECUTABLE``
#   Path to clang-tidy executable
# ``CLANG_TIDY_FOUND``
#   True if the clang-tidy executable was found.
# ``CLANG_TIDY_VERSION``
#   The version of clang-tidy found
# ``CLANG_TIDY_VERSION_MAJOR``
#   The clang-tidy major version if specified, 0 otherwise
# ``CLANG_TIDY_VERSION_MINOR``
#   The clang-tidy minor version if specified, 0 otherwise
# ``CLANG_TIDY_VERSION_PATCH``
#   The clang-tidy patch version if specified, 0 otherwise
# ``CLANG_TIDY_VERSION_COUNT``
#   Number of version components reported by clang-tidy
#
# Example usage:
#
# .. code-block:: cmake
#
#    find_package(ClangTidy)
#    if(CLANG_TIDY_FOUND)
#      message("clang-tidy executable found: ${CLANG_TIDY_EXECUTABLE}\n"
#              "version: ${CLANG_TIDY_VERSION}")
#    endif()

find_program(CLANG_TIDY_EXECUTABLE
  NAMES 
        clang-tidy-9.0 clang-tidy-9
        clang-tidy-8.0 clang-tidy-8
        clang-tidy-7.0 clang-tidy-7
        clang-tidy-6.0 clang-tidy-6
        clang-tidy clang-tidy-5.0
        clang-tidy-4.0 clang-tidy-3.9
        clang-tidy-3.8 clang-tidy-3.7
        clang-tidy-3.6 clang-tidy-3.5
        clang-tidy-3.4 clang-tidy-3.3
  DOC "clang-tidy executable"
)
mark_as_advanced(CLANG_TIDY_EXECUTABLE)

# Extract version from command "clang-tidy -version"
if(CLANG_TIDY_EXECUTABLE)
  execute_process(COMMAND sh -c "${CLANG_TIDY_EXECUTABLE} -version | grep version"
                  OUTPUT_VARIABLE clang_tidy_version
                  # ERROR_QUIET
                  OUTPUT_STRIP_TRAILING_WHITESPACE)

  if (clang_tidy_version MATCHES "version .*")
    # clang_tidy_version sample: "  LLVM version 3.9.1"
    string(REGEX REPLACE
           " *LLVM version ([.0-9]+).*" "\\1"
           CLANG_TIDY_VERSION "${clang_tidy_version}")
    # CLANG_TIDY_VERSION sample: "3.9.1"

    # Extract version components
    string(REPLACE "." ";" clang_tidy_version "${CLANG_TIDY_VERSION}")
    list(LENGTH clang_tidy_version CLANG_TIDY_VERSION_COUNT)
    if(CLANG_TIDY_VERSION_COUNT GREATER 0)
      list(GET clang_tidy_version 0 CLANG_TIDY_VERSION_MAJOR)
    else()
      set(CLANG_TIDY_VERSION_MAJOR 0)
    endif()
    if(CLANG_TIDY_VERSION_COUNT GREATER 1)
      list(GET clang_tidy_version 1 CLANG_TIDY_VERSION_MINOR)
    else()
      set(CLANG_TIDY_VERSION_MINOR 0)
    endif()
    if(CLANG_TIDY_VERSION_COUNT GREATER 2)
      list(GET clang_tidy_version 2 CLANG_TIDY_VERSION_PATCH)
    else()
      set(CLANG_TIDY_VERSION_PATCH 0)
    endif()
    if(CLANG_TIDY_VERSION_MAJOR LESS 6)
      message(FATAL_ERROR "Your installed clang-tidy version is too old! clang-tidy v6.0.0 or later is required!")
    endif()
  else()
    message(FATAL_ERROR "Could not detect version of installed clang-tidy!")
  endif()
  unset(clang_tidy_version)
else()
  message(FATAL_ERROR "Could not find clang-tidy! You need to install it first!")
endif()

if(CLANG_TIDY_EXECUTABLE)
  set(CLANG_TIDY_FOUND TRUE)
else()
  set(CLANG_TIDY_FOUND FALSE)
endif()
