# Lab 4

In this lab, your job will be to escape from a WebAssembly sandbox.
This will teach you to think about the kinds of vulnerabilities that
can arise in trying to isolate untrusted code.

## Code base

The code for this lab consists of three major parts:

- **The WebAssembly runtime.**  The runtime is responsible for executing
  WebAssembly code, in a way that is isolated from the rest of
  the system except for well-defined interfaces.  WebAssembly code
  consists of well-defined instructions, executed by this runtime;
  if you are curious, you can play around with individual WebAssembly
  instructions in MDN's interactive documentation, such as
  [this page on the `xor` instruction](https://developer.mozilla.org/en-US/docs/WebAssembly/Reference/Numeric/XOR),
  but this level of understanding is not necessary for this lab.

  We are using a somewhat inefficient but pure Python-based [WebAssembly
  interpreter](https://github.com/mohanson/pywasm).

- **The WASI (WebAssembly System Interface) module.**  This interface
  gives the WebAssembly module access to things outside of its isolated
  box, such as being able to access files.  The functions provided by
  the WASI module are precisely the "well-defined interfaces" that the
  WebAssembly module is allowed to invoke.  WASI is nominally specified
  [here](https://github.com/WebAssembly/WASI/blob/main/phases/snapshot/docs.md),
  but you will probably find it easier to just read our implementation instead.

  For security, the WASI module ensures that the WebAssembly code cannot
  access arbitrary parts of the system.  More specifically, the WASI
  module is given a root directory for the sandbox (say, something like
  `/tmp/sandbox`), and the WebAssembly code should have access to all
  of the files and directories under `/tmp/sandbox` but should not be
  able to get out of that directory.

  The WASI module is implemented in [wasi.py](wasi.py).  Our WASI
  module has some security issues in it, and it will be your goal to
  exploit them.

- **The shell that runs inside the WebAssembly runtime.**  We have
  provided a simple shell, resembling the Unix shell, that will run
  inside the WebAssembly sandbox.  The shell implementation is in
  [tinysh.c](tinysh.c), for your reference, but you will run the
  pre-compiled WebAssembly executable of this shell, `tinysh.wasm`.

  The shell is compiled together with the
  [wasi-libc](https://github.com/WebAssembly/wasi-libc) library, which
  turns standard C and POSIX operations like `malloc` and `open` into
  appropriate calls to the (simpler and narrower) WASI interface, but
  you should not need to dig into wasi-libc for this lab.

## Shell commands

Your specific job will be to run the shell inside the WebAssembly sandbox
and come up with shell commands that will let you access a secret file
called `secret.txt` one level of directory up from the sandbox.  To get
started, run `make shell` and try entering some commands:

```
nickolai@sonora:~/6.1600/lab-master/lab4$ make shell
. venv/bin/activate && python3 interactive.py
$ ls
.
..
$ cat ../secret.txt
open: Operation not permitted
$ help
unknown command help; available commands are:
  echo pwd cd ls cat mkdir rmdir rm touch mv cp ln fd_list fd_open fd_openat fd_close fd_read
$ 
```

Here you can see that the shell starts out with an empty directory, and
trying to naively read `../secret.txt` does not work: the WASI module
prevents it.  You can also see there are a number of Unix-like commands
available to you, as well as some lower-level commands that manipulate
file descriptors:

- `fd_list` lists the currently open file descriptors.
- `fd_open` opens a path name as a new file descriptor.
- `fd_openat` opens a path name relative to an existing directory file descriptor, as a new file descriptor.
- `fd_close` closes a file descriptor.
- `fd_read` reads and prints the data from a file descriptor (much like `cat`).

## Part 1: warm-up

For part 1, come up with a sequence of shell commands that read the
contents of the secret from `../secret.txt`, and save your commands to
`solution-1.txt`.  Hint: think about using a symlink.  You can check
your answer using `make grade`.

## Part 2: file descriptor invariants

For part 2, come up with a sequence of shell commands that read the contents
of the secret from `../secret.txt` without using the `ln` command to
create any symlinks, and save your commands to `solution-2.txt`.

In the absence of symlinks, you will have to uncover and exploit a deeper
problem in how our WASI module works.  The problem is more of an issue
with the design rather than the low-level implementation, so you might
be able to figure out the attack just from the following description
of how it works, although you may find it useful to refer to its source
code if something is unclear.  The mistake is related to the invariant
that the WASI module tries to maintain about file descriptors.

The WASI module maintains a map of open file descriptors in `self.fds`,
translating from an integer value (which is seen by the code running
inside the sandbox) to a Python object representing that file.  For open
files and directories, that Python object is an `OpenFile()`.  The key
invariant is that `OpenFile.depth` is supposed to represent the number
of levels of directory from that file or directory to the root of the
sandbox.  This `depth` value is used by `OpenFile.check_path()` to make
sure that, whenever the sandbox asks to open a file, the path name being
opened does not contain more `..` components than the current depth,
so that opening the path does not escape the sandbox's root.

In WASI, all operations that open a file by pathname use the `path_open()`
function provided by WASI to the sandbox.  This function always works
relative to a file descriptor of a starting directory.  When the sandboxed
code opens an absolute pathname, such as `open("/hello/world.txt", ...)`,
the `wasi-libc` implementation finds the file descriptor of the sandbox's
root directory (corresponding to the `Preopen()` file descriptor in
the `Wasi()` constructor), and invokes, roughly, `path_open(root_fd,
"hello/world.txt")`.  But if the sandboxed code invokes `openat(dirfd,
"world.txt")`, which means open the name `world.txt` in whatever directory
corresponds to `dirfd`, `wasi-libc` does not need to find the sandbox
root fd, and passes the arguments directly to WASI's `path_open()`.
You can see that the `depth` value for the sandbox root directory starts
out at 0, as specified in the `Preopen()` constructor.

To help you figure out what the bug is, and how to exploit it, first
think about what WASI operations might violate the above invariant,
and second, how would you take advantage of this invariant being violated?

You can check your answer using `make grade`.

## Submit your answers

Create a zip file containing `solution-1.txt` and `solution-2.txt`
and upload it to Gradescope.

