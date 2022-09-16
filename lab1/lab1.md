# 6.1600 Lab 1

In this lab you will design and implement a secure client synchronization protocol.

## Scenario

Consider the following setup.  Alice has two devices: a laptop and a mobile phone.  Both of these devices communicate with our server, which hosts our photo-sharing application.
```
Alice's laptop  <------>
                          Server
                                  <------> Alice's mobile phone
```

One feature we may wish to support is to allow Alice's laptop to synchronize its photos with her phone.  In particular, let's say that Alice posts a photo from her laptop.

```
                tim.jpg
Alice's laptop  ------->
                          Server
                                  ------ Alice's mobile phone
```

Later, she logs onto the application from her phone and downloads the photo for viewing.

```
Alice's laptop  ------
                        Server
                                ------>  Alice's mobile phone
                                tim.jpg
```

The devices can then both upload photos and the other will download them.

To enable this, our starter code uses a log-based system to synchronize _operations_ between devices. A cooperating server will store a single log, and a single client can post new entries to the log by making requests to the server. In our case, the two operations are:

1. `REGISTER`: Starts the log.
2. `PUT_PHOTO`: Add a new photo to the user's album.

The server will accept any arbitrary bytestring as a log entry. In our codebase, the client sends these log entries to the server in `Client.register` and `Client.put_photo` respectively by generating a `LogEntry`, encoding it as a bytestring (we have provided you with `LogEntry.encode`) and including the encoded log entry in an RPC call to the server. 

Another client can then download this log to _synchronize_ with the state of the server. In `Client._synchronize`, which is called before client functions that require server data, the client sends a `SynchronizeRequest` RPC to the server, and the server (assuming it is honest) replies with a list of all the log entries that it knows about. Since these are encoded as bytestrings, the client then decodes them into `LogEntry`s by calling `LogEntry.decode` (also provided to you). As it does so, it performs actions based on each log entry to update its own local state (primarily updating the local list of photos.)

Photo data itself is not included in the log to minimize the size of log entries. Instead, each `PUT_PHOTO` log entry contains a photo ID (`LogEntry.photo_id`) that can be used to request a given photo from the server's file store.

## Attacks
As long as the server and the network are honest, this provides correctness. However, for these labs our threat model includes a compromised server which can behave in any way---it can respond to our `SynchronizeRequest` with whatever our adversary likes. Unfortunately, our current implementation does not provide very strong _security_. Our goal is for the photo album received by a new device to be the same as the original, but the server is able to modify it in several ways. For example:

- A malicious server could replace our photo `tim.jpg` with `john.jpg` when we request a photo with a certain ID. 
- The server could add arbitrary new photos to our album by fabricating log entries.
- The server could delete a photo that it does not like by refusing to send the corresponding log entry to the client.
- The server could duplicate a photo by inserting the same log entry twice. 
- The server could show `tim_1.jpg` to one device and `tim_2.jpg` to another device for a certain ID by supplying different versions of a log entry to each device.

In this lab, we will be focused on avoiding these attacks. To do so, you will make use of hash functions and Message Authentication Codes as covered in lecture to authenticate the log from the server.

## More specifically

We assume that all of Alice's devices are able to share a secret (`user_secret` in `Client.__init__`) out-of-band---perhaps via a passphrase, over a separately authenticated channel.

Suppose Alice has two devices: `A` and `B`.

Suppose moreover that `A` issues a series of updates to the server, where the first update registers Alice with the server, and subsequent updates add her photos to the server.

Alice now logs into the server with `B`.  Alice calls `B.list_photos` and `B.get_photo` to view her pictures on her new device.

Alice can then upload photos from both `A` and `B` as she chooses.

A secure implementation of client synchronization guarantees the following, even with a malicious server:

 - For every photo ID `id` inside the list returned by `B.list_photos()`, `B.get_photo(id) == A.get_photo(id)`, and vice versa.
 - If device `A` shows a given change from device `B`, it must show all previous changes from device `B` as well, and vice versa. 

If at any point the client detects that the log has been modified by someone other than Alice (and thus cannot provide the above properties), it should raise an `errors.SynchronizationError`

Of course, we still require the system to behave _correctly_ given an honest server:
- With an honest server (e.g. `ReferenceServer`), `B.list_photos() == A.list_photos()`


### Your job

Your job is to add authentication to the `Client` in the `client` module, so that Alice's new device will be able to guarantee the properties above, even in the face of a malicious server.

_This is an open-ended assignment!_  In contrast to lab 0, you will be designing your own authentication protocol.  There are many different ways to solve this problem.  It may take a few iterations to converge to a good design.  We recommend you to start design work early and check in with the staff if you have questions!

You may modify any code in `client.py` so long as you do not change the signatures of the public methods of `Client` (i.e., the `__init__` method or methods not beginning with an underscore `_`).  However, since your `Client` must still talk to our server, you will **not** be able to modify any other files given to you.

To check your implementation, use `make grade-lab1`. 

Hints that may be useful to you:

 - It might be helpful to write out your scheme on paper before trying to implement it.
 - One common problem is producing a secure _but incorrect_ synchronization implementation which rejects good log entries (when the server is not misbehaving).  **It may help to run `make test` to debug these kinds of problems.**
 - The `common/crypto` module contains routines for creating message authentication codes and hashes of lists of data, given a `crypto.UserSecret`.
 - The RPC requests `types.PutPhotoRequest` and `types.RegisterRequest` both require a `bytes` encoding of a log entry, which can be obtained by calling `LogEntry.encode()`. If you choose to modify or replace the `LogEntry` class, you will need to be familiar with `codec.encode()`.  This transforms some Python object (dictionaries, lists, integers, strings, or bytes) into a single `bytes` encoding of that object and allows recreating the object with `codec.decode()`.
 - You can turn a `str` object `x` into a `bytes` object with the method `x.encode('utf-8')`.
 - There is some helper code in `client.py` which may help you as you build your solution, such as the `LogEntry` class.  They may help you to structure your solution.  You may find it useful to modify these.
 - We've provided a server that handles requests correctly.  Our autograder's server will not be as cooperative.
 - If you have issues with failing tests, you may find it helpful to inspect and alter the autograder source to assist you in the debugging process.  The autograder lives in the `ag/ag1` subdirectory.

Make sure to keep your solutions private, as per [the course collaboration policy](https://6s060.csail.mit.edu/2021/handouts/info_fall.pdf).  In particular, note that if you make a public fork of this repository on GitHub, any code you write there will also become public, so remember not to put your work into that fork.

### To submit lab 1

upload a ZIP file containing `client.py` to [Gradescope](https://www.gradescope.com/courses/281655).

