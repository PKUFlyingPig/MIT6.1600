# 6.1600 Labs

Most 6.1600 labs require implementing several features of a photo-sharing system, the skeleton of which we provide for you in this repository.

The general structure of this system includes a client, which you control, and a server which you do not control---imagine that the client is an application on your phone that connects to a cloud provider that you do not trust. Your job in each of the labs will be to enforce certain security properties within this client-server relationship.

## Code Overview
The system is structured as a client and a server that communicate via Remote Procedure Calls (RPCs) over HTTP. This code is split up into three main folders:

- `client`: Code that is exclusive to the client is stored here. This consists of only the client implementation itself, `Client` in `client.py`.
- `server`: Code that is exclusive to the server. This includes an interface defining the methods that a server should support as well as a reference server that follows the specification. Note, however, that there are no standards which a server your client interacts with will follow.
- `common`: Code that is shared between the client and server, such as types (including those that define the RPC interface) and cryptography functions. 

In your submission, you may edit only the code in `client/`.

There is also an autograder for your code. This is contained in the `ag/` folder.

## Installation
The labs are all written in python and require no installation beyond cloning the git repo. When running commands with the Makefile, a python virtual environment called `venv` will automatically be created for you, and the packages listed in `requirements.txt` for the corresponding lab will be installed.

### Dependencies 
These labs depend on Python 3.10 or later.  You can verify that your Python version is correct by running `python3 --version`, e.g.:
```
$ python3 --version
3.10.5
```

## Testing

### Functionality Tests

We have included some "doctests" to verify that our examples are correct. To run these tests for a lab, run `make test`, which will run Python [doctests](https://docs.python.org/3/library/doctest.html).  When the lab is complete, they should all pass, but they are not used for grading.

Note that these tests are different from the tests used by the autograder, which will be used to grade your assignments.

### Autograder
We will grade your lab using a set of tests contained in the `ag/` directory. To run these tests, you can use `make grade-lab0` for lab 0 and similar commands for the other labs.

Note that the autograder mocks out the HTTP interface (`ag/common/mock_http.py` and the `link_client_server()` calls you see in the doctests) to simplify testing. However, the client-server interactions should be exactly the same as if we were using an HTTP interface---please let us know if something seems wrong.

### Manual Testing
We encourage you to run tests manually after making a change to verify that it does what you intend. To do this, you need two terminal windows---one for the server and one for the client.

- Server: run `make run-server` to start the server. It will listen on the URL that it displays (likely `http://localhost:5000`). If you want to use a server other than the reference server, you can change the default server in `server/app.py` to point to a different implementation.
- Client: you can run the client from an interactive python window, a script, or whatever else you like. Notice that the client takes a `server_url` parameter when creating a `Client` instance---this should be the URL on which the server said it was listening.

## Assignments

You can find all the code required for each lab inside of its directory.  For instance, the code for [lab0](lab0/) resides in `lab0/`.

You can find the tasks for the corresponding assignment by looking at the Markdown file associated with the lab number.  The following files contain descriptions of the tasks for each lab:

 - [lab0](lab0/lab0.md)

Make sure to keep your solutions private, as per [the course collaboration policy](https://6s060.csail.mit.edu/2021/handouts/info_fall.pdf).  In particular, note that if you make a public fork of this repository on GitHub, any code you write there will also become public, so remember not to put your work into that fork.

## Feedback & Contributions

This is still a new class, and we are always working to improve the labs. If you find things that are annoying or that make it hard for you to effectively complete the labs and learn from them, please let us know. If you'd like to open a PR, feel free, but it probably be worthwhile to check with us before doing so to discuss your improvement.

