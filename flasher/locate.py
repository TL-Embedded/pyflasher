import os, shutil, sys

SEARCH_PATHS = [""]

IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform in ["linux", "linux2"]
IS_MAC = sys.platform in "darwin"


def expand_path(path: str):
    return os.path.normpath(os.path.expandvars(os.path.expanduser(path)))


def locate_file(fname: str):

    for search_path in SEARCH_PATHS:
        candidate = expand_path(os.path.join(search_path, fname))
        if os.path.isfile(candidate):
            return candidate
    
    raise FileNotFoundError(f"Cannot locate \"{fname}\"")


def locate_library(library: str):
    if IS_LINUX:
        library += ".so"
    elif IS_MAC:
        library += ".dylib"
    elif IS_WINDOWS:
        library += ".dll"
    else:
        raise LookupError("Unknown operating system")
    
    return locate_file(library)


def locate_executable(name: str):

    # If we can which it, then its fine
    path = shutil.which(name)
    if path:
        return path
    
    # Didnt work. Try to find the file on our search paths.
    if IS_WINDOWS:
        name += ".exe"
    
    return locate_file(name)


def add_search_path(path: str):
    global SEARCH_PATHS
    SEARCH_PATHS.insert(0, expand_path(path))