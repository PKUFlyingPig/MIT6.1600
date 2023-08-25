---
title: "Lab 3: Time and timing channels"
---

<style type="text/css">
    ol { list-style-type: upper-alpha; }
    ol ol { list-style-type: lower-roman; }
</style>


## Problem 1: Performance

In this problem, you will get some hands-on
experience with the performance characteristics of
different cryptographic algorithms.

For this lab, you will need access to a machine
with OpenSSL installed. The Athena machines will
work well for this if you don't have a convenient
local environment to use.
To test whether you are on a machine with OpenSSL,
run the shell command `openssl version`. You
should see some output like this:
```
$ openssl version
OpenSSL 3.0.7 1 Nov 2022 (Library: OpenSSL 3.0.7 1 Nov 2022)
```

Now, run `openssl help`. It should display some
output like this:
```
$ openssl help
help:

Standard commands
asn1parse         ca                ciphers           cmp
cms               crl               crl2pkcs7         dgst
dhparam           dsa               dsaparam          ec
ecparam           enc               engine            errstr
fipsinstall       gendsa            genpkey           genrsa
help              info              kdf               list
mac               nseq              ocsp              passwd
pkcs12            pkcs7             pkcs8             pkey
pkeyparam         pkeyutl           prime             rand
rehash            req               rsa               rsautl
s_client          s_server          s_time            sess_id
smime             speed             spkac             srp
storeutl          ts                verify            version
x509

Message Digest commands (see the `dgst' command for more details)
blake2b512        blake2s256        md4               md5
mdc2              rmd160            sha1              sha224
sha256            sha3-224          sha3-256          sha3-384
sha3-512          sha384            sha512            sha512-224
sha512-256        shake128          shake256          sm3

Cipher commands (see the `enc' command for more details)
aes-128-cbc       aes-128-ecb       aes-192-cbc       aes-192-ecb
aes-256-cbc       aes-256-ecb       aria-128-cbc      aria-128-cfb
aria-128-cfb1     aria-128-cfb8     aria-128-ctr      aria-128-ecb
aria-128-ofb      aria-192-cbc      aria-192-cfb      aria-192-cfb1
aria-192-cfb8     aria-192-ctr      aria-192-ecb      aria-192-ofb
aria-256-cbc      aria-256-cfb      aria-256-cfb1     aria-256-cfb8
aria-256-ctr      aria-256-ecb      aria-256-ofb      base64
bf                bf-cbc            bf-cfb            bf-ecb
bf-ofb            camellia-128-cbc  camellia-128-ecb  camellia-192-cbc
camellia-192-ecb  camellia-256-cbc  camellia-256-ecb  cast
cast-cbc          cast5-cbc         cast5-cfb         cast5-ecb
cast5-ofb         des               des-cbc           des-cfb
des-ecb           des-ede           des-ede-cbc       des-ede-cfb
des-ede-ofb       des-ede3          des-ede3-cbc      des-ede3-cfb
des-ede3-ofb      des-ofb           des3              desx
idea              idea-cbc          idea-cfb          idea-ecb
idea-ofb          rc2               rc2-40-cbc        rc2-64-cbc
rc2-cbc           rc2-cfb           rc2-ecb           rc2-ofb
rc4               rc4-40            seed              seed-cbc
seed-cfb          seed-ecb          seed-ofb          sm4-cbc
sm4-cfb           sm4-ctr           sm4-ecb           sm4-ofb
zlib
```

You can see benchmark each of the message-digest
and cipher algorithms listed here by running
`openssl speed <ALG_NAME>`. For example `openssl
speed rc4` will give you performance numbers for
the RC4 block cipher.

A few additional algorithms not listed above are:

* `rsa1024`, `rsa2048`, `rsa4096` -- RSA keypair
  generation and signing

* `ecdh` -- Elliptic-curve Diffie-Hellman key
  exchange

* `dsa` -- The digital signature algorithm,
  working over the integers modulo a prime p

* `ecsda` -- Elliptic-curve digital signature
  algorithm

In addition, the following command runs AES
encryption using hardware acceleration (if your
machine supports it), with a 256-bit key in Galois
counter mode:
```
openssl speed -evp aes-256-gcm
```

The command `openssl genrsa 4096` will generate
a 4096-bit keypair.

The command `openssl speed -help` will give you
more options that you can pass to the `speed`
command.

# Questions

1.  You are designing a file-storage application
    that requires computing a MAC over large
    files. You have the option between using
    HMAC-SHA256 and AES-128-GMAC. Both of these
    MACs give 128-bit security. Which has
    better performance for encrypting >1MB files?
    (You may have to do a little bit of research
    on the design of both of these primitives to 
    come up with a good answer.)

1.  Your boss tells you that to protect against
    quantum computers, your company will have to
    switch from using AES-128 encryption to
    AES-256 encryption. Roughly how much longer
    will it take to encrypt a 100MB file after
    increasing the key size? Explain why
    in at most three sentences.

1.  MIT has asked you to redesign the software on
    the MIT certificate authority (CA). They are
    deciding between using RSA, DSA, and ECDSA
    signatures.


    1.      What is the minimum keylength you must
            use for each of these three 
            signature algorithms to achieve 128-bit
            security under the best-known attacks today?

            Answer the following sub-questions
            assuming that you use key sizes for each algorithm
            that achieve 128-bit security.

    1.      Which of these three algorithms is
            fastest/slowest for signing?

    1.      Which of these three algorithms is
            fastest/slowest for signature verification?

    1.      Which of these three algorithms is
            fastest/slowest for keypair generation?
            (You should be able to infer the
            answer to this question from the
            output of the `openssl` commands given above.)
       
1.  MIT's Touchstone authentication service allows
    users to authenticated using a username and
    password. Which password-hashing function would you use 
    for storing hashed passwords on the server?
    Explain why in at most three sentences.

## Problem 2: Timing side-channel attack

In this problem you will mount your own attack to
extract a secret password from a server using an
insecure authentication scheme.

The code for this assignment is in [`timing`](https://github.com/mit-pdos/6.1600-labs/tree/main/timing).

# Scenario

Bob runs a payments service that, after Bob
authenticates by sending a password to the server,
runs the `send_money` routine to process
a payment. (In this toy example, `send_money` is
a no-op.)

In a secure implementation, Bob's server would use
a robust off-the-shelf authenticated transport
protocol (SSH, TLS 1.3 with pre-shared keys,
etc.). But since Bob has not taken 6.1600 yet, he
cooked up his own ad-hoc authentication protocol.

Bob's server accepts requests from the network,
where each request contains a password. Bob's
server checks the request's password against
the true password and calls the `send_money`
function only if the passwords match.

# More specifically

On initialization, a `BadServer` instance generates a secret password using fresh randomness and saves it as a hexadecimal string i.e., one with characters from `0` to `9` or `a` to `f`. Note **two** hexadecimal characters represent one byte of data.

The `BadServer` allows any user to submit a `VerifyRequest` with some password.
The server responds with a `VerifyResponse`, which contains a single boolean value.
This value is `True` if the password in the request matches the server's secret.
Otherwise, the value is `False`.

Implementation errors make it possible for you, the attacker, to violate this property.
In particular, software side channels (specifically, timing side channels) foil Bob's attempt to achieve this property.

# Your job

Your job is to implement `steal_password` in [`timing/attacker.py`](https://github.com/mit-pdos/6.1600-labs/tree/main/timeing/attacker.py) to steal the secret password from the server.

Timing side channels have nondeterministic behavior.
Thus, while we have provided an autograder to help you develop your solution locally, **you will need it to submit your solution to our autograder on Gradescope to receive an accurate evaluation.**

In particular,
 - The autograder will test whether you can extract passwords of different lengths.  The length **in bytes** is the `l` parameter to `steal_password`.
 - Every test will wait 20 minutes for the attacker to extract the secret password.  Your attack must complete by this time (or the autograder will reject it).
 - Your attack must not crash or fail (or the autograder will reject it).
 - To compute your final grade, the autograder will only be run a limited number of times per student.  Make sure that your attack succeeds with a comfortably-high probability.

Finally, you must not access private variables of
the `BadServer` instance. 


## Problem 3: Server performance

In this 
