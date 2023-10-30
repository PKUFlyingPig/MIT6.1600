import pywasm
import ctypes
import sys
import os
import stat
import errno
import _io
from typing import List, Union, Dict, Any, Callable, Optional, BinaryIO, overload

WASI_ERRNO_BADF = 8
WASI_ERRNO_INVAL = 28
WASI_ERRNO_ISDIR = 31
WASI_ERRNO_NOENT = 44
WASI_ERRNO_NOSYS = 52
WASI_ERRNO_NOTDIR = 54
WASI_ERRNO_PERM = 63

WASI_PREOPENTYPE_DIR = 0

WASI_FILETYPE_UNKNOWN = 0
WASI_FILETYPE_DIR = 3
WASI_FILETYPE_REG = 4
WASI_FILETYPE_SYMLINK = 7

WASI_FDFLAGS_APPEND = 1

WASI_OFLAGS_CREAT = (1 << 0)
WASI_OFLAGS_DIR = (1 << 1)
WASI_OFLAGS_EXCL = (1 << 2)
WASI_OFLAGS_TRUNC = (1 << 3)

WASI_LOOKUPFLAGS_SYMLINK_FOLLOW = (1 << 0)

def store(s: pywasm.Store, ptr: int, data: Union[ctypes.Structure, bytes]) -> None:
    ## convert any ctypes.Structure into actual bytes
    bdata = bytes(data)
    s.memory_list[0].data[ptr:ptr+len(bdata)] = bdata

def storestr(s: pywasm.Store, ptr: int, len: int, data: bytes) -> None:
    ## add a terminating NUL, but then truncate to len bytes
    data = (data + b'\x00')[:len]
    store(s, ptr, data)

def load(s: pywasm.Store, ptr: int, datatype: Any) -> Any:
    return datatype.from_buffer_copy(s.memory_list[0].data[ptr:])

def loadbytes(s: pywasm.Store, ptr: int, len: int) -> bytes:
    return bytes(s.memory_list[0].data[ptr:ptr+len])

filetype_t = ctypes.c_ubyte
size_t = ctypes.c_uint
fdflags_t = ctypes.c_ushort
rights_t = ctypes.c_ulonglong
timestamp_t = ctypes.c_ulonglong
device_t = ctypes.c_ulonglong
inode_t = ctypes.c_ulonglong
linkcount_t = ctypes.c_ulonglong
filesize_t = ctypes.c_ulonglong
dircookie_t = ctypes.c_ulonglong

class prestat_t(ctypes.Structure):
    _fields_ = [
        ("tag", ctypes.c_ubyte),
        ("dir", size_t),
    ]

class fdstat_t(ctypes.Structure):
    _fields_ = [
        ("filetype", filetype_t),
        ("fdflags", fdflags_t),
        ("rights_base", rights_t),
        ("rights_inheriting", rights_t),
    ]

class ciovec_t(ctypes.Structure):
    _fields_ = [
        ("buf", ctypes.c_uint),
        ("buf_len", size_t),
    ]

class filestat_t(ctypes.Structure):
    _fields_ = [
        ("dev", device_t),
        ("ino", inode_t),
        ("filetype", filetype_t),
        ("nlink", linkcount_t),
        ("size", filesize_t),
        ("atim", timestamp_t),
        ("mtim", timestamp_t),
        ("ctim", timestamp_t),
    ]

class dirent_t(ctypes.Structure):
    _fields_ = [
        ("next", dircookie_t),
        ("ino", inode_t),
        ("namelen", size_t),
        ("type", filetype_t),
    ]

def stat_to_filestat_t(st: os.stat_result) -> filestat_t:
    res = filestat_t()
    if stat.S_ISREG(st.st_mode):
        res.filetype = WASI_FILETYPE_REG
    elif stat.S_ISDIR(st.st_mode):
        res.filetype = WASI_FILETYPE_DIR
    elif stat.S_ISLNK(st.st_mode):
        res.filetype = WASI_FILETYPE_SYMLINK
    else:
        res.filetype = WASI_FILETYPE_UNKNOWN
    res.size = st.st_size
    return res

def wasi_oflags_to_flags(oflags: int) -> int:
    flags = 0
    if oflags & WASI_OFLAGS_CREAT: flags |= os.O_CREAT
    if oflags & WASI_OFLAGS_DIR:   flags |= os.O_DIRECTORY
    if oflags & WASI_OFLAGS_EXCL:  flags |= os.O_EXCL
    if oflags & WASI_OFLAGS_TRUNC: flags |= os.O_TRUNC
    return flags

def oserror_errno(e: OSError) -> int:
    match e.errno:
        case errno.ENOENT:
            return WASI_ERRNO_NOENT
        case errno.ENOTDIR:
            return WASI_ERRNO_NOTDIR
        case errno.EISDIR:
            return WASI_ERRNO_ISDIR
        case errno.EPERM:
            return WASI_ERRNO_PERM
        case errno.EBADF:
            return WASI_ERRNO_BADF
        case _:
            return WASI_ERRNO_INVAL

def catch_errors(f: Callable[..., int]) -> Callable[..., int]:
    def inner(*args: Any, **kwargs: Any) -> int:
        try:
            return f(*args, **kwargs)
        except OSError as e:
            return oserror_errno(e)
    return inner

class ConsoleFd:
    def __init__(self, f):
        self.f = f

    def write(self, b: bytes) -> int:
        res = self.f.buffer.write(b)
        self.f.buffer.flush()
        return res

    def read(self, n: int) -> bytes:
        return self.f.buffer.read(min(n, 1))

## This is purposely insecure for the purposes of lab4.
##
## The right way to prevent .. escape is to use openat2(RESOLVE_BENEATH).
class OpenFile:
    def __init__(self, fd: int, depth: int):
        self.fd = fd
        self.depth = depth

    def write(self, b: bytes) -> int:
        return os.write(self.fd, b)

    def read(self, n: int) -> bytes:
        return os.read(self.fd, n)

    def check_path(self, pn: bytes) -> int:
        depth = self.depth
        for n in pn.split(b'/'):
            if n == b'' or n == b'.':
                continue
            if n == b'..':
                if depth <= 0:
                    raise OSError(errno.EPERM, 'Permission denied')
                depth -= 1
                continue
            depth += 1
        return depth

class Preopen(OpenFile):
    def __init__(self, guestname: bytes, hostname: bytes):
        super().__init__(os.open(hostname, os.O_RDONLY), 0)
        self.guestname = guestname

class Wasi:
    def __init__(self, args: List[str] = [], verbose: bool = False, rootdir: Optional[str] = None):
        self.fds: Dict[int, Union[ConsoleFd, Preopen, OpenFile]] = {
            0: ConsoleFd(sys.stdin),
            1: ConsoleFd(sys.stdout),
            2: ConsoleFd(sys.stderr),
        }
        if rootdir is not None:
            self.fds[3] = Preopen(b'/', rootdir.encode('utf-8'))
        self.verbose = verbose
        self.args = args

    def trace(self, op: str, *args: Any) -> None:
        if self.verbose:
            print(op, *args)

    def unimpl(self, name: str) -> Callable[..., int]:
        def do(s: pywasm.Store, *args: Any) -> int:
            self.trace("unimpl", name, args)
            return WASI_ERRNO_NOSYS
        return do

    def get_fd(self, fd: int, expect_type: Optional[type] = None) -> Union[ConsoleFd, Preopen, OpenFile]:
        if fd not in self.fds:
            raise OSError(errno.EBADF, 'Bad file descriptor')
        f = self.fds[fd]
        if expect_type is not None and not isinstance(f, expect_type):
            raise OSError(errno.EINVAL, 'Invalid argument')
        return f

    def alloc_fd(self, obj: OpenFile) -> int:
        fd = 0
        while True:
            if fd not in self.fds:
                self.fds[fd] = obj
                return fd
            fd += 1

    def fd_prestat_get(self, s: pywasm.Store, fd: int, retptr: int) -> int:
        self.trace("fd_prestat_get", fd)
        f = self.get_fd(fd, Preopen)
        res = prestat_t()
        res.tag = WASI_PREOPENTYPE_DIR
        res.dir = len(f.guestname)
        store(s, retptr, res)
        return 0

    def fd_prestat_dir_name(self, s: pywasm.Store, fd: int, path: int, pathlen: int) -> int:
        self.trace("fd_prestat_dir_name", fd)
        f = self.get_fd(fd, Preopen)
        storestr(s, path, pathlen, f.guestname)
        return 0

    def fd_fdstat_get(self, s: pywasm.Store, fd: int, ptr: int) -> int:
        self.trace("fdstat_get", fd)
        f = self.get_fd(fd)
        res = fdstat_t()
        if isinstance(f, OpenFile):
            try:
                st = os.fstat(f.fd)
                res.filetype = stat_to_filestat_t(st).filetype
            except IOError:
                res.filetype = WASI_FILETYPE_UNKNOWN
        else:
            res.filetype = WASI_FILETYPE_UNKNOWN
        return 0

    def fd_filestat_get(self, s: pywasm.Store, fd: int, retptr: int) -> int:
        self.trace("fd_filestat_get", fd)
        f = self.get_fd(fd)
        if isinstance(f, OpenFile):
            st = os.fstat(f.fd)
            res = stat_to_filestat_t(st)
        else:
            res = filestat_t()
        store(s, retptr, res)
        return 0

    def fd_read(self, s: pywasm.Store, fd: int, iovs: int, iovs_len: int, retptr: int) -> int:
        self.trace("fd_read", fd, iovs_len)
        f = self.get_fd(fd)
        cc = 0
        for i in range(0, iovs_len):
            iov = load(s, iovs, ciovec_t)
            data = f.read(iov.buf_len)
            if data is None or len(data) == 0:
                break
            store(s, iov.buf, data)
            cc += len(data)
            if len(data) < iov.buf_len:
                break
            iovs += ctypes.sizeof(iov)
        store(s, retptr, size_t(cc))
        return 0

    def fd_write(self, s: pywasm.Store, fd: int, iovs: int, iovs_len: int, retptr: int) -> int:
        self.trace("fd_write", fd, iovs_len)
        f = self.get_fd(fd)
        cc = 0
        for i in range(0, iovs_len):
            iov = load(s, iovs, ciovec_t)
            data = loadbytes(s, iov.buf, iov.buf_len)
            n = f.write(data)
            cc += n
            if n < len(data):
                break
            iovs += ctypes.sizeof(iov)
        store(s, retptr, size_t(cc))
        return 0

    def fd_readdir(self, s: pywasm.Store, fd: int, buf: int, buflen: int, cookie: int, retsize: int) -> int:
        self.trace("fd_readdir", fd, buf, buflen, cookie, retsize)
        f = self.get_fd(fd, OpenFile)

        ## portable but inefficient implementation
        names = sorted([".", ".."] + os.listdir(f.fd))

        bnames: List[bytes] = [n.encode('utf-8', 'ignore') for n in names]
        dirent = dirent_t()
        cc = 0
        while buflen >= cc + ctypes.sizeof(dirent):
            if cookie >= len(bnames):
                break
            dirent.next = cookie+1
            dirent.ino = 0
            dirent.namelen = len(bnames[cookie])
            dirent.type = WASI_FILETYPE_UNKNOWN
            store(s, buf+cc, dirent)
            cc += ctypes.sizeof(dirent)
            namelen = min(buflen-cc, len(bnames[cookie]))
            store(s, buf+cc, bnames[cookie][:namelen])
            cc += namelen
            cookie += 1

        store(s, retsize, size_t(cc))
        return 0

    def fd_close(self, s: pywasm.Store, fd: int) -> int:
        self.trace("fd_close", fd)
        f = self.get_fd(fd)
        if isinstance(f, OpenFile):
            os.close(f.fd)
        del self.fds[fd]
        return 0

    def path_create_directory(self, s: pywasm.Store, fd: int, pathptr: int, pathlen: int) -> int:
        p = loadbytes(s, pathptr, pathlen)
        self.trace("path_create_directory", fd, p)
        f = self.get_fd(fd, OpenFile)
        f.check_path(p)
        os.mkdir(p, dir_fd = f.fd)
        return 0

    def path_remove_directory(self, s: pywasm.Store, fd: int, pathptr: int, pathlen: int) -> int:
        p = loadbytes(s, pathptr, pathlen)
        self.trace("path_remove_directory", fd, p)
        f = self.get_fd(fd, OpenFile)
        f.check_path(p)
        os.rmdir(p, dir_fd = f.fd)
        return 0

    def path_unlink_file(self, s: pywasm.Store, fd: int, pathptr: int, pathlen: int) -> int:
        p = loadbytes(s, pathptr, pathlen)
        self.trace("path_unlink_file", fd, p)
        f = self.get_fd(fd, OpenFile)
        f.check_path(p)
        os.unlink(p, dir_fd = f.fd)
        return 0

    def path_rename(self, s: pywasm.Store, old_fd: int, old_path_ptr: int, old_path_len: int, new_fd: int, new_path_ptr: int, new_path_len: int) -> int:
        old_path = loadbytes(s, old_path_ptr, old_path_len)
        new_path = loadbytes(s, new_path_ptr, new_path_len)
        self.trace("path_rename", old_fd, old_path, new_fd, new_path)
        oldf = self.get_fd(old_fd, OpenFile)
        newf = self.get_fd(new_fd, OpenFile)
        oldf.check_path(old_path)
        newf.check_path(new_path)
        os.rename(old_path, new_path, src_dir_fd = oldf.fd, dst_dir_fd = newf.fd)
        return 0

    def path_filestat_get(self, s: pywasm.Store, fd: int, flags: int, pathptr: int, pathlen: int, retptr: int) -> int:
        p = loadbytes(s, pathptr, pathlen)
        self.trace("path_filestat_get", fd, p, flags)
        f = self.get_fd(fd, OpenFile)
        f.check_path(p)

        if flags & WASI_LOOKUPFLAGS_SYMLINK_FOLLOW:
            st = os.stat(p, dir_fd = f.fd)
        else:
            st = os.lstat(p, dir_fd = f.fd)
        res = stat_to_filestat_t(st)
        store(s, retptr, res)
        return 0

    def path_open(self, s: pywasm.Store, dirfd: int, dirflags: int, pathptr: int, pathlen: int, oflags: int, rbase: int, rinherit: int, fdflags: int, retfd: int) -> int:
        path = loadbytes(s, pathptr, pathlen)
        self.trace("path_open", dirfd, path)
        f = self.get_fd(dirfd, OpenFile)
        depth = f.check_path(path)

        flags = wasi_oflags_to_flags(oflags)
        newfd = os.open(path, flags, dir_fd = f.fd)
        newf = OpenFile(newfd, depth)
        fd = self.alloc_fd(newf)
        store(s, retfd, ctypes.c_int(fd))
        return 0

    def path_symlink(self, s: pywasm.Store, target_ptr: int, target_len: int, fd: int, pathptr: int, pathlen: int) -> int:
        target = loadbytes(s, target_ptr, target_len)
        p = loadbytes(s, pathptr, pathlen)
        self.trace("path_symlink", fd, target, p)
        f = self.get_fd(fd, OpenFile)
        f.check_path(p)
        os.symlink(target, p, dir_fd = f.fd)
        return 0

    def path_readlink(self, s: pywasm.Store, fd: int, pathptr: int, pathlen: int, buf: int, buflen: int, retptr: int) -> int:
        path = loadbytes(s, pathptr, pathlen)
        self.trace("path_readlink", fd, path)
        f = self.get_fd(fd, OpenFile)
        res = os.readlink(path, dir_fd = f.fd)
        storestr(s, buf, buflen, res)
        store(s, retptr, ctypes.c_int(len(res)))
        return 0

    def args_sizes_get(self, s: pywasm.Store, argc: int, argv_buf_size: int) -> int:
        self.trace("args_sizes_get")
        store(s, argc, size_t(len(self.args)))
        store(s, argv_buf_size, size_t(sum([len(s) + 1 for s in self.args])))
        return 0

    def args_get(self, s: pywasm.Store, argv: int, argv_buf: int) -> int:
        self.trace("args_get", argv, argv_buf)
        for arg in self.args:
            store(s, argv, size_t(argv_buf))
            storestr(s, argv_buf, len(arg)+1, arg)
            argv = argv + 4
            argv_buf = argv_buf + len(arg) + 1
        return 0

    def environ_sizes_get(self, s: pywasm.Store, nvar: int, nbytes: int) -> int:
        self.trace("environ_sizes_get")
        store(s, nvar, size_t(0))
        store(s, nbytes, size_t(0))
        return 0

    def environ_get(self, s: pywasm.Store, env: int, envbuf: int) -> int:
        self.trace("environ_get")
        return 0

    def clock_res_get(self, s: pywasm.Store, clockid: int, ts: int) -> int:
        self.trace("clock_res_get", clockid)
        return WASI_ERRNO_INVAL

    def clock_time_get(self, s: pywasm.Store, clockid: int, prec: int, ts: int) -> int:
        self.trace("clock_time_get", clockid)
        return WASI_ERRNO_INVAL

    def random_get(self, s: pywasm.Store, buf: int, buflen: int) -> int:
        self.trace("random_get", buflen)
        store(s, buf, os.urandom(buflen))
        return 0

    def proc_exit(self, s: pywasm.Store, rval: int) -> int:
        exit(rval)

    def imports(self) -> Dict[str, Any]:
        funcs: Dict[str, Callable[..., int]] = {
            "args_get": self.args_get,
            "args_sizes_get": self.args_sizes_get,
            "environ_get": self.environ_get,
            "environ_sizes_get": self.environ_sizes_get,
            "clock_res_get": self.clock_res_get,
            "clock_time_get": self.clock_time_get,
            "fd_advise": self.unimpl("fd_advise"),
            "fd_allocate": self.unimpl("fd_allocate"),
            "fd_close": self.fd_close,
            "fd_datasync": self.unimpl("fd_datasync"),
            "fd_fdstat_get": self.fd_fdstat_get,
            "fd_fdstat_set_flags": self.unimpl("fd_fdstat_set_flags"),
            "fd_fdstat_set_rights": self.unimpl("fd_fdstat_set_rights"),
            "fd_filestat_get": self.fd_filestat_get,
            "fd_filestat_set_size": self.unimpl("fd_filestat_set_size"),
            "fd_filestat_set_times": self.unimpl("fd_filestat_set_times"),
            "fd_pread": self.unimpl("fd_pread"),
            "fd_prestat_get": self.fd_prestat_get,
            "fd_prestat_dir_name": self.fd_prestat_dir_name,
            "fd_pwrite": self.unimpl("fd_pwrite"),
            "fd_read": self.fd_read,
            "fd_readdir": self.fd_readdir,
            "fd_renumber": self.unimpl("fd_renumber"),
            "fd_seek": self.unimpl("fd_seek"),
            "fd_sync": self.unimpl("fd_sync"),
            "fd_tell": self.unimpl("fd_tell"),
            "fd_write": self.fd_write,
            "path_create_directory": self.path_create_directory,
            "path_filestat_get": self.path_filestat_get,
            "path_filestat_set_times": self.unimpl("path_filestat_set_times"),
            "path_link": self.unimpl("path_link"),
            "path_open": self.path_open,
            "path_readlink": self.path_readlink,
            "path_remove_directory": self.path_remove_directory,
            "path_rename": self.path_rename,
            "path_symlink": self.path_symlink,
            "path_unlink_file": self.path_unlink_file,
            "poll_oneoff": self.unimpl("poll_oneoff"),
            "proc_exit": self.proc_exit,
            "sched_yield": self.unimpl("sched_yield"),
            "random_get": self.random_get,
            "sock_accept": self.unimpl("sock_accept"),
            "sock_recv": self.unimpl("sock_recv"),
            "sock_send": self.unimpl("sock_send"),
            "sock_shutdown": self.unimpl("sock_shutdown"),
        }
        return { name: catch_errors(funcs[name]) for name in funcs }
