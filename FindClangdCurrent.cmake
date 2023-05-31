#
#.rst:
# FindClangd
# ---------------
#
# The module defines the following variables
#
# ``CLANGD_EXECUTABLE``
#   Path to clangd executable
# ``CLANGD_FOUND``
#   True if the clangd executable was found.
# ``CLANGD_VERSION``
#   The version of clangd found
# ``CLANGD_VERSION_MAJOR``
#   The clangd major version if specified, 0 otherwise
# ``CLANGD_VERSION_MINOR``
#   The clangd minor version if specified, 0 otherwise
# ``CLANGD_VERSION_PATCH``
#   The clangd patch version if specified, 0 otherwise
# ``CLANGD_VERSION_COUNT``
#   Number of version components reported by clangd
#
# Example usage:
#
# .. code-block:: cmake
#
#    find_package(Clangd)
#    if(CLANGD_FOUND)
#      message("clangd executable found: ${CLANGD_EXECUTABLE}\n"
#              "version: ${CLANGD_VERSION}")
#    endif()

find_program(CLANGD_EXECUTABLE
  NAMES
        clangd-20 clangd-19
        clangd-18 clangd-17
        clangd-16 clangd-15
        clangd-14 clangd-13
        clangd-12 clangd-11
        clangd-10 clangd-9
        clangd-8.0 clangd-8
        clangd-7.0 clangd-7
        clangd-6.0 clangd-6
        clangd clangd-5.0
        clangd-4.0 clangd-3.9
        clangd-3.8 clangd-3.7
        clangd-3.6 clangd-3.5
        clangd-3.4 clangd-3.3
  DOC "clangd executable"
)
mark_as_advanced(CLANGD_EXECUTABLE)

# Extract version from command "clangd -version"
if(CLANGD_EXECUTABLE)
  execute_process(COMMAND sh -c "${CLANGD_EXECUTABLE} -version | grep version"
                  OUTPUT_VARIABLE clangd_version
                  # ERROR_QUIET
                  OUTPUT_STRIP_TRAILING_WHITESPACE)

  if (clangd_version MATCHES "version .*")
    # clangd_version sample: "  LLVM version 3.9.1"
    string(REGEX REPLACE
           " *LLVM version ([.0-9]+).*" "\\1"
           CLANGD_VERSION "${clangd_version}")
    # CLANGD_VERSION sample: "3.9.1"

    # Extract version components
    string(REPLACE "." ";" clangd_version "${CLANGD_VERSION}")
    list(LENGTH clangd_version CLANGD_VERSION_COUNT)
    if(CLANGD_VERSION_COUNT GREATER 0)
      list(GET clangd_version 0 CLANGD_VERSION_MAJOR)
    else()
      set(CLANGD_VERSION_MAJOR 0)
    endif()
    if(CLANGD_VERSION_COUNT GREATER 1)
      list(GET clangd_version 1 CLANGD_VERSION_MINOR)
    else()
      set(CLANGD_VERSION_MINOR 0)
    endif()
    if(CLANGD_VERSION_COUNT GREATER 2)
      list(GET clangd_version 2 CLANGD_VERSION_PATCH)
    else()
      set(CLANGD_VERSION_PATCH 0)
    endif()
    if(CLANGD_VERSION_MAJOR LESS 6)
      message(FATAL_ERROR "Your installed clangd version is too old! clangd v6.0.0 or later is required!")
    endif()
  else()
    message(FATAL_ERROR "Could not detect version of installed clangd!")
  endif()
  unset(clangd_version)
else()
  message(FATAL_ERROR "Could not find clangd! You need to install it first!")
endif()

if(CLANGD_EXECUTABLE)
  set(CLANGD_FOUND TRUE)
else()
  set(CLANGD_FOUND FALSE)
endif()
