import ctypes
import os
import subprocess
import shutil
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
_C_SRC = os.path.join(_REPO, "native", "Sources", "CLuna", "luna.c")
_C_INC = os.path.join(_REPO, "native", "Sources", "CLuna", "include")
_BUILD_LIB = os.path.join(_REPO, "native", "build", "libluna.dylib")
_CACHE_LIB = os.path.expanduser("~/.cache/luna/libluna.dylib")
class _Pkg(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char_p),
        ("url", ctypes.c_char_p),
        ("commit", ctypes.c_char_p),
        ("config", ctypes.c_char_p),
        ("compile", ctypes.c_char_p),
        ("install", ctypes.c_char_p),
        ("installed", ctypes.c_int),
    ]
_LOG_CB = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_void_p)
_lib = None
def _candidate_paths():
    env = os.environ.get("LUNA_LIB", "")
    if env:
        yield env
    yield _BUILD_LIB
    yield _CACHE_LIB
    for p in ("/opt/homebrew/lib/libluna.dylib", "/usr/local/lib/libluna.dylib"):
        yield p
def _try_load(path):
    try:
        if path and os.path.isfile(path):
            return ctypes.CDLL(path)
    except OSError:
        return None
    return None
def _build_lib(dest):
    if not os.path.isfile(_C_SRC):
        return False
    cc = shutil.which("cc") or shutil.which("clang") or "cc"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    cmd = [cc, "-std=c11", "-O2", "-fPIC", "-shared", f"-I{_C_INC}", _C_SRC, "-o", dest]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return os.path.isfile(dest)
    except Exception:
        return False
def _ensure_lib():
    global _lib
    if _lib is not None:
        return _lib
    for p in _candidate_paths():
        lib = _try_load(p)
        if lib is not None:
            _lib = lib
            break
    if _lib is None:
        if _build_lib(_BUILD_LIB):
            _lib = _try_load(_BUILD_LIB)
        if _lib is None and _build_lib(_CACHE_LIB):
            _lib = _try_load(_CACHE_LIB)
    if _lib is None:
        raise OSError("libluna not found and auto-build failed; install a C compiler and ensure native/Sources/CLuna/luna.c exists")
    _lib.luna_version.restype = ctypes.c_char_p
    _lib.luna_last_error.restype = ctypes.c_char_p
    _lib.luna_clear_error.argtypes = []
    _lib.luna_set_root.argtypes = [ctypes.c_char_p]
    _lib.luna_set_root.restype = ctypes.c_int
    _lib.luna_add.argtypes = [ctypes.c_char_p] * 5
    _lib.luna_add.restype = ctypes.c_int
    _lib.luna_remove.argtypes = [ctypes.c_char_p]
    _lib.luna_remove.restype = ctypes.c_int
    _lib.luna_get.argtypes = [ctypes.c_char_p, ctypes.POINTER(_Pkg)]
    _lib.luna_get.restype = ctypes.c_int
    _lib.luna_free_package.argtypes = [ctypes.POINTER(_Pkg)]
    _lib.luna_list.argtypes = [ctypes.POINTER(ctypes.POINTER(_Pkg)), ctypes.POINTER(ctypes.c_size_t)]
    _lib.luna_list.restype = ctypes.c_int
    _lib.luna_free_list.argtypes = [ctypes.POINTER(_Pkg), ctypes.c_size_t]
    _lib.luna_get_remote_commit.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_size_t]
    _lib.luna_get_remote_commit.restype = ctypes.c_int
    _lib.luna_needs_update.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
    _lib.luna_needs_update.restype = ctypes.c_int
    _lib.luna_install.argtypes = [ctypes.c_char_p, _LOG_CB, ctypes.c_void_p]
    _lib.luna_install.restype = ctypes.c_int
    _lib.luna_update_all.argtypes = [ctypes.POINTER(ctypes.c_int), _LOG_CB, ctypes.c_void_p]
    _lib.luna_update_all.restype = ctypes.c_int
    return _lib
def _b(s):
    if s is None:
        return b""
    if isinstance(s, bytes):
        return s
    return str(s).encode()
def _s(b):
    if b is None:
        return ""
    if isinstance(b, bytes):
        return b.decode(errors="replace")
    return str(b)
def version():
    return _s(_ensure_lib().luna_version())
def last_error():
    return _s(_ensure_lib().luna_last_error())
def set_root(path=""):
    lib = _ensure_lib()
    rc = lib.luna_set_root(_b(path) if path else None)
    if rc != 0:
        raise RuntimeError(last_error() or "luna_set_root failed")
def add(name, url, compile_cmd="", config_cmd="", install_cmd=""):
    lib = _ensure_lib()
    rc = lib.luna_add(_b(name), _b(url), _b(compile_cmd), _b(config_cmd), _b(install_cmd))
    if rc != 0:
        raise RuntimeError(last_error() or "luna_add failed")
def remove(name):
    lib = _ensure_lib()
    rc = lib.luna_remove(_b(name))
    if rc != 0:
        raise RuntimeError(last_error() or "luna_remove failed")
def get(name):
    lib = _ensure_lib()
    pkg = _Pkg()
    rc = lib.luna_get(_b(name), ctypes.byref(pkg))
    if rc != 0:
        raise RuntimeError(last_error() or "luna_get failed")
    try:
        return {
            "name": _s(pkg.name),
            "url": _s(pkg.url),
            "commit": _s(pkg.commit),
            "config": _s(pkg.config),
            "compile": _s(pkg.compile),
            "install": _s(pkg.install),
            "installed": bool(pkg.installed),
        }
    finally:
        lib.luna_free_package(ctypes.byref(pkg))
def list_packages():
    lib = _ensure_lib()
    ptr = ctypes.POINTER(_Pkg)()
    count = ctypes.c_size_t(0)
    rc = lib.luna_list(ctypes.byref(ptr), ctypes.byref(count))
    if rc != 0:
        raise RuntimeError(last_error() or "luna_list failed")
    out = []
    try:
        for i in range(count.value):
            p = ptr[i]
            out.append({
                "name": _s(p.name),
                "url": _s(p.url),
                "commit": _s(p.commit),
                "config": _s(p.config),
                "compile": _s(p.compile),
                "install": _s(p.install),
                "installed": bool(p.installed),
            })
        return out
    finally:
        if ptr:
            lib.luna_free_list(ptr, count.value)
def get_remote_commit(url):
    lib = _ensure_lib()
    buf = ctypes.create_string_buffer(256)
    rc = lib.luna_get_remote_commit(_b(url), buf, ctypes.c_size_t(256))
    if rc != 0:
        raise RuntimeError(last_error() or "get_remote_commit failed")
    return _s(buf.value)
def needs_update(name):
    lib = _ensure_lib()
    flag = ctypes.c_int(0)
    rc = lib.luna_needs_update(_b(name), ctypes.byref(flag))
    if rc != 0:
        raise RuntimeError(last_error() or "needs_update failed")
    return bool(flag.value)
def install(name, log_cb=None):
    lib = _ensure_lib()
    cb = None
    if log_cb is not None:
        def _wrap(msg, _ctx):
            try:
                log_cb(_s(msg))
            except Exception:
                pass
        cb = _LOG_CB(_wrap)
    rc = lib.luna_install(_b(name), cb, None)
    if rc != 0:
        raise RuntimeError(last_error() or "install failed")
    if cb is not None:
        try:
            ctypes.cast(cb, ctypes.c_void_p)
        except Exception:
            pass
def update_all(log_cb=None):
    lib = _ensure_lib()
    cb = None
    if log_cb is not None:
        def _wrap(msg, _ctx):
            try:
                log_cb(_s(msg))
            except Exception:
                pass
        cb = _LOG_CB(_wrap)
    updated = ctypes.c_int(0)
    rc = lib.luna_update_all(ctypes.byref(updated), cb, None)
    if rc != 0:
        raise RuntimeError(last_error() or "update failed")
    return int(updated.value)
