project(git-clang-format-cmake)
cmake_minimum_required(VERSION 3.3)

find_package(Git REQUIRED)
find_package(PythonInterp REQUIRED)

set(GCF_DIR ${CMAKE_CURRENT_LIST_DIR} PARENT_SCOPE)

macro(GCF_CHECK_OPTION_OR_DEFAULT ARG_NAME DEFAULT)
  if(NOT DEFINED GCF_${ARG_NAME})
    if(NOT DEFINED GCF_GLOBAL_${ARG_NAME})
      set(GCF_${ARG_NAME} ${DEFAULT})
    else()
      set(GCF_${ARG_NAME} ${GCF_GLOBAL_${ARG_NAME}})
    endif()
  endif()
endmacro()

function(create_git_hook)
  set(options ABORT_COMMIT)
  set(oneValueArgs FORMAT_STYLE MODES IGNORE_DIRS TIDY_CHECKS cpp_FORMATTERS cpp_LINTERS cmake_FORMATTERS cmake_LINTERS py_FORMATTERS py_LINTERS)
  set(multiValueArgs "")
  cmake_parse_arguments(GCF "${options}" "${oneValueArgs}"
                        "${multiValueArgs}" ${ARGN} )

  set(GCF_SCRIPT ${GCF_DIR}/git-cmake-format.py)
  set(GCF_BUILD_DIR "${CMAKE_BINARY_DIR}")
  set(GCF_SOURCE_DIR "${CMAKE_SOURCE_DIR}")

  if(NOT DEFINED GCF_IGNORE_DIRS)
    set(GCF_IGNORE_DIRS "")
  endif()
  if(NOT ${GCF_ABORT_COMMIT})
    unset(GCF_ABORT_COMMIT)
  endif()

  # clang-format style
  GCF_CHECK_OPTION_OR_DEFAULT("CLANG_FORMAT_STYLE" "file")
  # Checks executed by clang-tidy
  GCF_CHECK_OPTION_OR_DEFAULT("CLANG_TIDY_CHECKS"
    "readability-*,bugprone-*,modernize-*,google-*")
  # Comma-separated list of tools to run
  GCF_CHECK_OPTION_OR_DEFAULT("MODES" "format,lint")
  # Abort commit if files would be formatted
  GCF_CHECK_OPTION_OR_DEFAULT("ABORT_COMMIT" FALSE)

  # Comma-separated lists of formatters/linters for specific file types
  GCF_CHECK_OPTION_OR_DEFAULT("cpp_FORMATTERS" "clang-format")
  GCF_CHECK_OPTION_OR_DEFAULT("cpp_LINTERS" "clang-tidy")
  GCF_CHECK_OPTION_OR_DEFAULT("cmake_FORMATTERS" "") # cmake-format
  GCF_CHECK_OPTION_OR_DEFAULT("cmake_LINTERS" "")
  GCF_CHECK_OPTION_OR_DEFAULT("py_FORMATTERS" "") # autopep8
  GCF_CHECK_OPTION_OR_DEFAULT("py_LINTERS" "") # pylint

  string(REPLACE "," ";" GCF_cpp_FORMATTERS_LIST "${GCF_cpp_FORMATTERS}")
  string(REPLACE "," ";" GCF_cpp_LINTERS_LIST "${GCF_cpp_LINTERS}")
  string(REPLACE "," ";" GCF_cmake_FORMATTERS_LIST "${GCF_cmake_FORMATTERS}")
  string(REPLACE "," ";" GCF_cmake_LINTERS_LIST "${GCF_cmake_LINTERS}")
  string(REPLACE "," ";" GCF_py_FORMATTERS_LIST "${GCF_py_FORMATTERS}")
  string(REPLACE "," ";" GCF_py_LINTERS_LIST "${GCF_py_LINTERS}")

  list(APPEND CMAKE_MODULE_PATH ${GCF_DIR})
  if("clang-format" IN_LIST GCF_cpp_FORMATTERS_LIST)
    find_package(ClangFormat REQUIRED)
  endif()
  if("cmake-format" IN_LIST GCF_cmake_FORMATTERS_LIST)
    find_program(GCF_CMAKE_FORMAT_PATH cmake-format REQUIRED)
  endif()
  if("autopep8" IN_LIST GCF_py_FORMATTERS_LIST)
    find_program(GCF_AUTOPEP_PATH autopep8 REQUIRED)
  endif()

  if("clang-tidy" IN_LIST GCF_cpp_LINTERS_LIST)
    find_package(ClangTidy REQUIRED)
  endif()
  if("pylint" IN_LIST GCF_py_LINTERS_LIST)
    find_program(GCF_PYLINT_PATH pylint REQUIRED)
  endif()

  execute_process(COMMAND ${GIT_EXECUTABLE} rev-parse --show-toplevel
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    OUTPUT_VARIABLE GCF_GIT_ROOT
    OUTPUT_STRIP_TRAILING_WHITESPACE)

  # --absolute-git-dir is not supported on git=2.7.3 which is installed on Ubuntu 16.04
  execute_process(COMMAND sh -c "readlink -f $(${GIT_EXECUTABLE} rev-parse --git-dir)"
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    OUTPUT_VARIABLE GCF_GIT_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE)

  if(NOT GCF_GIT_ROOT)
    message(WARNING "Not in a git repository")
  else()
    configure_file(
      "${GCF_DIR}/pre-commit.template.sh"
      "${GCF_GIT_DIR}/hooks/pre-commit"
      @ONLY)

    get_filename_component(GCF_PROJECT_NAME "${CMAKE_BINARY_DIR}" NAME)
    configure_file(
      "${GCF_DIR}/project.template.yaml"
      "${GCF_GIT_DIR}/hooks/.${GCF_PROJECT_NAME}.config.yaml"
      @ONLY)

    configure_file(
      "${GCF_DIR}/run_hooks.template.sh"
      "${GCF_GIT_ROOT}/run_hooks"
      @ONLY)
  endif()
endfunction()
