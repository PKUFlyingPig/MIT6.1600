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

To clone the repo, first make sure you have `git` installed, and then run the command `https://github.com/mit-pdos/6.1600-labs.git`. To update once you have already cloned, use `git pull`.

### For Linux/macOS
We have provided a Makefile that reduces the number of commands you need to remember and that handles creating the virtual environment for you. These generally take the form `grade-labX`, as discussed in the Autograder section.

For manual testing, you should activate the venv before running tests to ensure that you are using the correct dependencies. From the lab directory, run:

`source ./venv/bin/activate`

If the `venv` folder does not yet exist, any of the `make` commands will make it for you. You can type `make venv` to build the venv without running the autograder. The virtual environment will stay active (as indicated by `(venv)` somewhere in your prompt, unless you have modified it) until you type `deactivate`.

### For Windows
For Windows, the venv must be created manually and activated in order to run the autograder or any manual tests. To do this, navigate to the lab directory using `cd` (e.g. `cd C:\Users\security\school\6.1600\lab0`) and run the following commands:

1. To verify python version (>= 3.10.x): `python -V`
2. To create the virtual environment: `python -m venv venv`
3. To activate the virtual environment: `venv/Scripts/activate`
    - Note: if you are using powershell, you may need to follow [these](https://docs.microsoft.com/en-us/previous-versions//bb613481(v=vs.85)?redirectedfrom=MSDN) instructions to allow running scripts. You may also need to use the command as `./venv/Scripts/activate`.
    - With the virtual environment activated, you should see `(venv)` somewhere in your prompt (unless you have customized your prompt).
4. To install dependencies (with the venv active): `pip install -r requirements.txt`

When this completes, you are all set! You will need to repeat this process for each lab. Once you have the virtual environment created and the dependencies installed, you can activate it at any time by following step 3 above. It will stay active until you type `deactivate` or until you close your terminal session. To run the autograder commands below or to run the client/server in manual tests, you will need the venv activated.

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
We will grade your lab using a set of tests contained in the `ag/` directory. To run these tests, you can use `make grade-lab0` (on linux) or `python grade-lab.py --lab=0` (on windows, with the venv activated) for lab 0 and similar commands for the other labs.

Note that the autograder mocks out the HTTP interface (`ag/common/mock_http.py` and the `link_client_server()` calls you see in the doctests) to simplify testing. However, the client-server interactions should be exactly the same as if we were using an HTTP interface---please let us know if something seems wrong.

### Manual Testing
We encourage you to run tests manually after making a change to verify that it does what you intend. To do this, you need two terminal windows---one for the server and one for the client.

- Server: run `make run-server` to start the server. It will listen on the URL that it displays (likely `http://localhost:5000`). If you want to use a server other than the reference server, you can change the default server in `server/app.py` to point to a different implementation.
- Client: you can run the client from an interactive python window, a script, or whatever else you like. Notice that the client takes a `server_url` parameter when creating a `Client` instance---this should be the URL on which the server said it was listening.

## Assignments

You can find all the code required for each lab inside of its directory.  For instance, the code for [lab0](lab0/) resides in `lab0/`.

You can find the tasks for the corresponding assignment by looking at the Markdown file associated with the lab number.  The following files contain descriptions of the tasks for each lab:

 - [lab0](lab0/lab0.md)
 - [lab1](lab1/lab1.md)
 - [lab2](lab2/lab2.md)
 - [lab3](lab3/lab3.md)
 - [lab4](lab4/lab4.md)
 - [lab5](lab5/lab5.md)

Make sure to keep your solutions private, as per the course collaboration policy (see the course info handout).  In particular, note that if you make a public fork of this repository on GitHub, any code you write there will also become public, so remember not to put your work into that fork.

## Feedback & Contributions

This is still a new class, and we are always working to improve the labs. If you find things that are annoying or that make it hard for you to effectively complete the labs and learn from them, please let us know. If you'd like to open a PR, feel free, but it probably be worthwhile to check with us before doing so to discuss your improvement.

