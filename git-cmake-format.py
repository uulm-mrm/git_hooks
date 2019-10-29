#!/usr/bin/python

from __future__ import print_function
import os
import subprocess
import sys
import argparse
import yaml
import os
import six
from os.path import normpath, normcase
import fnmatch
from termcolor import colored

formatter_patterns = {
    'cpp': ['*.h', '*.cpp', '*.hpp', '*.c', '*.cc', '*.hh', '*.cxx', '*.hxx'],
    'cmake': ['CMakeLists.txt', '*.cmake'], # '*.cmake.in', '*.cmake.installspace.in', '*.cmake.develspace.in'
    'py': ['*.py']
}
linter_patterns = {
    'cpp': ['*.cpp', '*.c', '*.cc', '*.cxx'],
    'cmake': ['CMakeLists.txt', '*.cmake', '*.cmake.in', '*.cmake.installspace.in', '*.cmake.develspace.in'],
    'py': ['*.py']
}

def callFormatter(formatter_name, project, files):
    if not formatter_name in project.keys() or project[formatter_name] is None:
        print("Formatter {} is not configured! Cannot run this formatter!".format(formatter_name))
        sys.exit(1)
    if formatter_name == 'clang-format':
        _args = [project[formatter_name], '-style', project["clang_format_style"]]
        if len(files) == 1 and not isinstance(files[0], six.string_types):
            ret = subprocess.Popen(_args, stdin=files[0], stdout=subprocess.PIPE)
            return ret.stdout.read()
        else:
            subprocess.check_call(_args + ['-i'] + files)
    elif formatter_name == 'cmake-format':
        _args = [project[formatter_name], '--enable-markup', '0']
        if len(files) == 1 and not isinstance(files[0], six.string_types):
            ret = subprocess.Popen(_args, stdin=files[0], stdout=subprocess.PIPE)
            return ret.stdout.read()
        else:
            subprocess.check_call(_args + ['-i'] + files)
    elif formatter_name == 'autopep8':
        _args = [project[formatter_name]]
        if len(files) == 1 and not isinstance(files[0], six.string_types):
            ret = subprocess.Popen(_args, stdin=files[0], stdout=subprocess.PIPE)
            return ret.stdout.read()
        else:
            subprocess.check_call(_args + ['-i'] + files)
    else:
        print('Unknown formatter (' + formatter_name + ')!')
        raise Exception()

def callLinter(linter_name, project, files):
    if not linter_name in project.keys() or project[linter_name] is None:
        print("Linter {} is not configured! Cannot run this linter!".format(linter_name))
        sys.exit(1)
    linter_args = [project[linter_name]]
    if linter_name == 'clang-tidy':
        if project["clang_tidy_checks"] is not None:
            linter_args.extend(['-checks=' + project["clang_tidy_checks"]])
        linter_args.extend(['-p', project["builddir"]])
        if args.fix:
            linter_args.extend(['--fix', '-format-style', project["clang_format_style"]])
        linter_args.extend(files)
    elif linter_name == 'pylint':
        linter_args.extend(files)
    else:
        print('Unknown linter (' + linter_name + ')!')
        raise Exception()
    subprocess.check_call(linter_args)

def getGitHead():
    RevParse = subprocess.Popen(['git', 'rev-parse', '--verify', 'HEAD'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    RevParse.communicate()
    if RevParse.returncode:
        return '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
    else:
        return 'HEAD'

def getGitRoot():
    RevParse = subprocess.Popen(['git', 'rev-parse', '--show-toplevel'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return RevParse.stdout.read().decode().strip()

def getGitDir():
    RevParse = subprocess.Popen(['git', 'rev-parse', '--git-dir'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return RevParse.stdout.read().decode().strip()

def getEditedFiles():
    Head = getGitHead()
    GitArgs = \
        ['git', 'diff-index', '--cached', '--diff-filter=ACMR', '--name-only', Head] \
        if args.mode != 'all' else \
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard']
    DiffIndex = subprocess.Popen(GitArgs, stdout=subprocess.PIPE)
    DiffIndexRet = DiffIndex.stdout.read().strip()
    DiffIndexRet = DiffIndexRet.decode()

    return DiffIndexRet.split('\n') if DiffIndexRet != "" else []

def getUnstagedFiles():
    Head = getGitHead()
    GitArgs = ['git', 'diff', '--stat']
    DiffIndex = subprocess.Popen(GitArgs, stdout=subprocess.PIPE)
    DiffIndexRet = DiffIndex.stdout.read().strip()
    DiffIndexRet = DiffIndexRet.decode()

    files = DiffIndexRet.split('\n')[:-1] if DiffIndexRet != "" else []
    files = [f.split(' | ')[0].strip() for f in files]
    return files

def matchesPattern(File, patterns):
    File = os.path.split(File)[1]
    return any([fnmatch.fnmatch(File, pattern) for pattern in patterns])

def is_subdir(path, directory):
    """
    Returns true if *path* in a subdirectory of *directory*.
    """
    path = normpath(normcase(path))
    directory = normpath(normcase(directory))
    if len(path) > len(directory):
        sep = os.path.sep.encode('ascii') if isinstance(directory, bytes) else os.path.sep
        if path.startswith(directory.rstrip(sep) + sep):
            return True
    return False

def is_ignored(path, ignore_list):
    for Dir in ignore_list:
        if '' != Dir and '' != os.path.commonprefix([os.path.relpath(path), os.path.relpath(Dir)]):
            return True
    return False

def formatFiles(projects):
    filesToFormat = []
    for project in projects:
        if not hasMode(args, project, 'format'):
            continue
        for f_type, files in project["formattable_files"].items():
            if len(files) == 0:
                continue
            for formatter_name in project[f_type + "_formatters"]:
                if project["abort_commit"] and args.hook:
                    filesToFormat.extend([f for f in files if requiresFormat(f, f_type, project)])
                    continue
                sys.stdout.write('Formatting ' + f_type + ' files of ' + project["name"] + " with " + formatter_name + "... ")
                sys.stdout.flush()
                callFormatter(formatter_name, project, files)
                print('done')
            if not project["abort_commit"] and args.hook:
                addFiles(files)
    return filesToFormat

def lintFiles(projects):
    for project in projects:
        if not hasMode(args, project, 'lint'):
            continue
        for f_type, files in project["source_files"].items():
            if len(files) == 0:
                continue
            for linter_name in project[f_type + "_linters"]:
                sys.stdout.write('Running ' + f_type + ' linter ' + linter_name + ' for ' + project["name"] + "... ")
                sys.stdout.flush()
                callLinter(linter_name, project, files)
                print('done')
            addFiles(files)

def addFiles(files):
    if len(files) > 0:
        subprocess.check_call(['git', 'add'] + files)

def hasMode(args, project, mode):
    modes = args.modes if not args.hook else project["modes"]
    return mode in modes

def requiresFormat(fileName, f_type, project):
    with open(fileName, 'r') as f:
        content = f.read()
        for formatter in project[f_type + "_formatters"]:
            f.seek(0)
            formattedContent = callFormatter(formatter, project, [f])
            if formattedContent != content:
                return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', dest='mode', action='store_const',
                        const='all', default='pre-commit',
                        help='Run on all files, not just commited files')
    parser.add_argument('--modes', dest='modes', type=str,
                        default='format,lint', help='Comma-separated list of tools to run. Possible values: format, lint. Default: format,lint')
    parser.add_argument('--fix', dest='fix', action='store_const', const=True, default=False,
                        help='Allow linters to fix lint errors')
    parser.add_argument('--hook', dest='hook', action='store_const',
                        const=True, default=False,
                        help='Enables hook mode (respects project modes)')

    args = parser.parse_args()
    args.modes = args.modes.split(',')
    for mode in args.modes:
        if mode != "format" and mode != "lint":
            print("Invalid mode: " + mode, file=sys.stderr)
            sys.exit(1)

    NoLint = False
    if 'LINT' in os.environ.keys() and int(os.environ['LINT']) == 0:
        NoLint = True

    GitRoot = getGitRoot()

    EditedFiles = getEditedFiles()
    UnstagedFiles = getUnstagedFiles()

    if len(EditedFiles) < 1:
        sys.exit(0)

    EditedFiles = list(map(lambda f: os.path.join(GitRoot, f), EditedFiles))
    UnstagedFiles = list(map(lambda f: os.path.join(GitRoot, f), UnstagedFiles))

    common = set(EditedFiles) & set(UnstagedFiles)
    if len(common) != 0:
        print(colored("Warning: The following files have only been added partially, they will be ignored because they cannot be formatted partially!", 'yellow'))
        for f in common:
            print("  ", colored(f[len(GitRoot)+1:], 'yellow'))
        EditedFiles = list(set(EditedFiles) - common)

    def load_project_config(filename):
        with open(filename, 'r') as f:
            try:
                return yaml.load(f, Loader=yaml.SafeLoader)
            except yaml.YAMLError as exc:
                print("Could not read project YAML file!")
                print(filename)
                print(exc)
                sys.exit(1)

    GitDir = getGitDir()
    projects = []
    for root, dirs, files in os.walk(GitDir):
        for name in files:
            if name.startswith(".") and name.endswith(".yaml"):
                filename = os.path.join(root, name)
                projects.append(load_project_config(filename))
    manualConfig = os.path.join(GitDir, "..", "git_hooks_config.yaml")
    if os.path.isfile(manualConfig):
        projects.append(load_project_config(manualConfig))

    for project in projects:
        project["modes"] = project["modes"].split(',')
        for f_type in formatter_patterns.keys():
            project[f_type + "_formatters"] = project[f_type + "_formatters"].split(',') if project[f_type + "_formatters"] is not None else []
        for f_type in linter_patterns.keys():
            project[f_type + "_linters"] = project[f_type + "_linters"].split(',') if project[f_type + "_linters"] is not None else []
        ignore = project["ignore"].split(':') if project["ignore"] is not None else []
        _matchesPattern = lambda patterns: lambda f: is_subdir(f, project["srcdir"]) and \
            not is_ignored(f, ignore) and matchesPattern(f, patterns)
        project["formattable_files"] = {}
        project["source_files"] = {}
        for f_type, patterns in formatter_patterns.items():
            project["formattable_files"][f_type] = list(filter(_matchesPattern(patterns), EditedFiles))
        for f_type, patterns in linter_patterns.items():
            project["source_files"][f_type] = list(filter(_matchesPattern(patterns), EditedFiles))
    total_len = lambda _dict: sum([len(l) for l in _dict.values()])
    projects = filter(lambda p: total_len(p["source_files"]) > 0 or total_len(p["formattable_files"]) > 0, projects)

    try:
        filesToFormat = formatFiles(projects)
        if len(filesToFormat) > 0:
            print('', file=sys.stderr)
            print('The following files need formatting and you enabled the \'abort commit\' option. Run \'./run_hooks --modes format\' manually.', file=sys.stderr)
            for f in filesToFormat:
                print('  ' + f, file=sys.stderr)
            sys.exit(1)
        if not args.hook or not NoLint:
            lintFiles(projects)
    except subprocess.CalledProcessError as e:
        print('', file=sys.stderr)
        print('An error occured, aborting commit...', file=sys.stderr)
        sys.exit(1)

    sys.exit(0)
