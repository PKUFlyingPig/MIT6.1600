---
title: "Lab 2: Bad randomness"
---

<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

<style type="text/css">
    ol { list-style-type: lower-alpha; }
    ol ol { list-style-type: circle; }
</style>


**Instructions on how to submit Lab 2:**
Please download all the required files from the [lab2 github repo](https://github.com/mit-pdos/6.1600-labs/tree/main/bad-random/).

* **Problem 0:** Please complete the True/False questions in the [lab0-problem0 gradescope assignment](https://www.gradescope.com/courses/533302/assignments/3287458/).

* **Code:** Place your code answers in the template [`ecdsa/sol.py`](https://github.com/mit-pdos/6.1600-labs/tree/main/bad-random/ecdsa/sol.py) for ecdsa questions and [`wep/attacker.py`](https://github.com/mit-pdos/6.1600-labs/tree/main/bad-random/wep/attacker.py).
    Please include all code necessary to generate your solution in each of the respective methods. Do not just hard code working answers!

* **Text:** Place your written answers in the template [`questions.txt`](https://github.com/mit-pdos/6.1600-labs/tree/main/bad-random/questions.txt)

Upload all files (`sol.py`, `attacker.py`, `questions.txt`) to the [lab2 gradescope assignment](https://www.gradescope.com/courses/533302/assignments/3287458/).

**Running the Lab on Windows**
`make check` and `make venv` do not natively work on Windows.

If you are using a windows machine, please see the [Windows Instructions](https://github.com/mit-pdos/6.1600-labs/tree/main/merkle/windows-instructions.md).

**Gradescope autograder:**
Your code will be graded with the Gradescope autograder with a total timeout of 40 minutes.

There is a STRICT 6.0GB memory limit on Gradescope. Reasonable solutions to this lab should not come close to approaching this memory limit.


**Plagiarism:** Gradescope automatically
runs a surprisingly effective 
plagiarism-detection tool on your
submissions. Please do not copy code from your
fellow students. Refer to the "Collaboration"
section of the [course
info](https://61600.csail.mit.edu/2023/handouts/info.pdf)
document for details on what types of
collaboration are and aren't allowed in 6.1600.
If you are having trouble completing an assignment
for whatever reason, _please_ ask the course staff
for help. We are often happy to give help and,
in many cases, extensions too! 
We are not happy when we find copied code.

# Problem 0: True/False

Please complete the True/False questions in the [lab0-problem0 gradescope assignment](https://www.gradescope.com/courses/533302/assignments/3287458/).

For these problems, let $$F \colon \{0,1\}^n \times \{0,1\}^n \to \{0,1\}^n$$ 
be a pseudorandom function. Let $$n \approx 256$$ be the security parameter.

1.  The function $$F'(k) := F(k, 0)$$ must be
    a one-way function.

1.  The function $$F'(k) := F(0, k)$$ must be
    a one-way function.

1.  The function $$F'(k) := F(k, 0) \| k $$ 
    must be a one-way function.

1.  A one-way function must be collision
    resistant.

1.  If $$\mathsf{MAC}(k,m)$$ is a secure MAC, then
    $$\mathsf{MAC}(k,m)$$ must be a pseudorandom function.

1.  The function $$\mathsf{MAC}(k,m) := F(k,m)$$
    is a secure MAC with message space $$\{0,1\}^n$$.

1.  The function $$\mathsf{MAC}(k,m) := F(k,\textbf{0}^{n-1}\|m)$$
    is a secure MAC with message space $$\{0,1\}$$,
    where $$\textbf{0}^{n-1}$$ is a string of $$n-1$$ zeros.

1.  The function $$\mathsf{MAC}(k,m) := k \oplus m$$
    is a secure MAC.

1.  Let $$H \colon \{0,1\}^* \to \{0,1\}^\ell$$ be a collision-resistant hash function.
    There is a collision-finding attack on $$H$$ that runs in time roughly $$2^{\ell/2}$$.

1.  If $$\Sigma$$ is a secure digital signature
    scheme (using the definition from lecture), then 
    $$\Sigma$$ remains secure even if an adversary can
    obtain many signatures on messages of its
    choice.

1.  If $$\Sigma$$ is a secure digital signature
    scheme (using the definition from lecture), then 
    $$\Sigma$$ remains secure even if an adversary can
    obtain half of the bits of the secret signing key.

1.  It is possible to use the ``hash-and-sign''
    paradigm with Lamport signatures.

1.  The RSA full-domain-hash signature scheme is
    proven secure under the RSA assumption and
    the assumption that the hash function is
    collision reistant.

1.  A Lamport signature on an $$n$$ bit message
    requires $$\lambda^2 n$$ bits to represent, 
    where $$\lambda$$ is the output length of
    the one-way function.

1.  There are in principle efficient
    (polynomial-time) attacks
    that break all known one-way functions on 
    a quantum computer.

1.  There are in principle efficient
    (polynomial-time) attacks
    that break RSA on a quantum computer.

# Problem 1: Bad randomness in key generation

The file
[`ecdsa/keygen.py`](https://github.com/mit-pdos/6.1600-labs/tree/main/bad-random/ecdsa/keygen.py)
generates an ECDSA signing keypair and prints the
resulting public key to standard output.

1.  The public keys generated using this script
    are insecure, in the sense that it is possible
    to recover the secret signing key given only the
    public verification key.

    Your task is to write a program, `problem_1a` in `sol.py`,
    that:
    
    *  takes a date (formatted as
    `YYYY-MM-DD`) as a single command-line argument,

    * reads a public key, generated by 
    `ecdsa/keygen.py`, from standard input, and

    * outputs the corresponding secret key, formatted as
    a base-10 integer.


    For example, on August 16, 2023 we generated a key...
    ```
    $ python keygen.py > key.txt
    -----BEGIN PUBLIC KEY-----
    MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEQfbUYzbQUiQWHcOtcmf/cVr+ygHI
    hs560RKiVUV0gqm4OyNLB+HCSf8c7mGzxDuuid8z3RkdXC9vw1e6tDuSRg==
    -----END PUBLIC KEY-----
    ```

    Later on, we should be able to use `problem_3a` to
    recover the secret key...
    ```
    $ problem_3a(2023-08-16,key.txt)
    88928882924258032953987945121779605092553192944307381616887680985059143398985
    ```

    Run `make check` to test your solution.

    _Hint:_ Your program should not require more than a few
    minutes of compute time.

    _Hint:_ If you are running on a multicore machine, 
    use as many cores as you can!


1. Your friend proposes instead reading `N` bytes
   of randomness from `/dev/random` and using 
   these bytes as the seed used to generate a 
   256-bit ECDSA keypair.

    For which values of `N` is this approach secure?
    (Indicate all that apply.)

    * 4 bytes

    * 16 bytes

    * 32 bytes

    * 256 bytes



# Problem 2: Bad randomness in ECDSA

ECDSA is one of the most widely used
digital-signature schemes.
ECDSA is a randomized signature scheme;
generating each ECDSA signature requires
the signer to sample a fresh random signing nonce.

See Chapter 19.3 of [Boneh-Shoup book](https://toc.cryptobook.us/book.pdf)
for a detailed description of ECDSA.
You should think of an ECDSA signature as being
computed as:

$$s \gets(H(m) + f(g^{\alpha_\text{t}}) \cdot \alpha)/\alpha_\text{t} \in \mathbb{Z}_q$$,

where:

* $$q \in \mathbb{Z}$$ is a fixed 256-bit prime,

* $$m \in \{0,1\}^*$$ is the message to be signed,

* $$H\colon \{0,1\}^* \to \mathbb{Z}_q$$ is a hash
  function,

* $$g$$ is the generator of and order-$$q$$ group
  $$\mathbb{G}$$,

* $$\alpha_\text{t} \in \mathbb{Z}_q$$ is the
  signing nonce,

* $$\alpha \in \mathbb{Z}_q$$ is the signer's
  secret key, and

* $$f \colon \mathbb{G} \to \mathbb{Z}_q$$ is
some function fixed in the ECDSA standard.

Throughout this problem, we assume that ECDSA 
signatures are always computed using the P256
elliptic curve, where the order $$q$$ is a 256-bit
integer.


1.  Say that an attacker can obtain two valid
    ECDSA signatures $$(r_0, s_0)$$, $$(r_1, s_1)$$
    that were generated using the same secret key
    $$\alpha$$ and signing nonce $$\alpha_\text{t}$$.

    Show how an attacker can use these signatures
    to recover the signer's secret key $$\alpha$$.
    In particular, write an expression for $$\alpha$$ 
    in terms of the other quantities.

    _Hint:_ Your attack should not need to use
    any properties of elliptic curves.

    _Hint:_ Appendix A.2 of the Boneh-Shoup book
    has helpful background about arithmetic modulo $$q$$.



1.  Write a program, in `problem_2b()` that takes as input two ECDSA signatures,
    signed using the same nonce, the hashes of the two messages signed, and outputs the signer's secret key.
    
    The input to problem_2b will be two tuple signatures (in the form `(r,s)`) as well as `H(m1)` and `H(m2)` (converted to an integer) for example:
    
    ```
    sig1 = (3373270495537608166420301124031645059552155087339817978895, 
    4866115514576831317719439267655910857343196914135233616904)

    sig2 = (3373270495537608166420301124031645059552155087339817978895,
    1026436076375142414773366823398026947727009880581933863772)

    Hm1 = 549937035807590235590408220127762782653536091071
    Hm2 = 111625161468258865202361239710433310078751980605
    ```
    Each `(r,s)` pair is one ECDSA signature. 
    The order `q` of the NIST curve is listed here for your
    convenience.
    ```
    q=6277101735386680763835789423176059013767194773182842284081
    ```

1.  In the ECDSA specification, $$\alpha_\text{t}$$
    is a uniformly random integer in the range
    $$\{1, 2, 3, \dots, q-1\}$$, where $$q \approx 2^{256}$$
    is the group order.
    Since ECDSA in this setting is only supposed to provide
    128-bit security, you might think that it
    would be safe to instead sample the signing nonce
    $$\alpha_\text{t}$$ as a random number in the range
    $$\{1, \dots, 2^{128}\}$$.
    Call this modified system "BadECDSA".
    
    Show that after an attacker obtains $$2^{64}$$
    BadECDSA signatures, it can recover the
    signer's secret key with constant probability.
    Therefore BadECDSA can have at most 64-bit security.


# Problem 3: Security issues in the WEP encryption scheme

The early versions of wifi used the WEP standard
to encrypt wireless network traffic.
In this problem, we will explore a few weaknesses of the WEP standard.

WEP encrypts each packet ("data frame") using
the RC4 stream cipher. Given a secret key $$k$$,
the RC4 cipher generates a long sequence of
pseudorandom bytes -- the "keystream". To encrypt a message
we XOR these bytes with the message. To decrypt,
we XOR these bytes with the ciphertext.


1.  For the RC4 secret key, the WEP endpoints use
    a long-term secret (typically of 40 or 104
    bits), concatenated with a 24-bit random
    initialization vector (IV).
    The long-term secret is fixed -- it is the 
    wifi password -- but the IV changes with each
    data frame.

    Each 802.11b data frame is at most 2312 bytes
    and an 802.11b network has a theoretical
    maximum throughput of 11 megabits per second.
    Roughly how long will an attacker have to wait
    to see two frames encrypted using the same IV,
    assuming a busy network operating at maximum
    capacity?

    What information can an attacker learn when 
    this occurs?

1.  WEP uses an insecure "hash-then-encrypt"
    scheme for integrity protection. In
    particular, the sender sends the 
    RC4 encryption of $$(m \| \text{Hash}(m))$$
    to the recipient. To check message integrity,
    the recipient decrypts the frame to get $$(m \| h)$$
    and accepts the packet if $$\text{Hash}(m) = h$$.

    Show that if the attacker intercepts a data
    frame containing the encryption of a known
    plaintext $$m$$, the attacker can trick the 
    recipient into accepting a message (of length
    $$|m|$$) of the attacker's choosing.

    Implement your attack as `attack_one` in
    [`wep/attacker.py`](https://github.com/mit-pdos/6.1600-labs/tree/main/bad-random/wep/attacker.py).
    The precise encryption scheme used by WEP is
    implemented by `send_packet()` in [`wep/victim.py`](https://github.com/mit-pdos/6.1600-labs/tree/main/bad-random/wep/victim.py).

1.  WEP uses the CRC32 non-cryptographic hash 
    function to compute the message-integrity hash.

    The CRC32 hash function has the property that 
    $$\text{CRC32}(x) \oplus \text{CRC32}(y) \oplus \text{CRC32}(z) = \text{CRC32}(x \oplus y \oplus z)$$.
    Explain how an attacker can abuse this property 
    to XOR bytes of its choice into
    a WEP-encrypted data frame, _even without knowing_
    the message that the frame encrypts.

    Implement your attack as `attack_two` in
    [`wep/attacker.py`](https://github.com/mit-pdos/6.1600-labs/tree/main/bad-random/wep/attacker.py).

1.  *Extra credit (challenging)*: A WEP recipient who receives a data frame with
    an invalid integrity hash will complain, while
    a recipient who receives a valid data frame
    will not. Explain how an attacker can use this
    information to extract the entire contents of
    an encrypted frame.
    
    Implement your attack as `attack_three` in
    [`wep/attacker.py`](https://github.com/mit-pdos/6.1600-labs/tree/main/bad-random/wep/attacker.py).

    _Hint_: Think about resizing the packet that
    the attacker intercepts.

    _Hint_: The fastest attack will exploit some
    structural properties of the CRC32 checksum.
    You will have to do some research to figure it
    out.
    

# Extra credit: Bad randomness in GMAC

Read Chapter 9.7 of [Boneh-Shoup book](https://toc.cryptobook.us/book.pdf),
which is about the AES-GCM mode of operation.
AES is by far the most widely used cipher today
and GCM is a popular modern mode of operation,
used in TLS 1.3 and many other places.

This problem will demonstrate that bad randomness
is catastrophic for AES-GCM: if the sender of a
message reuses an encryption nonce even once, an
attacker can break the CCA security of the
encryption scheme.

1. Say that an attacker intercepts a GCM
   ciphertext $$(c,t)$$ and is somehow able
   to obtain the GHASH key $$k_\text{m}$$
   used to generate this ciphertext.

   Explain how the attacker can use its knowledge
   of $$k_\text{m}$$ to break the CCA security of
   AES-GCM.

1. Say that an attacker intercepts a pair of
   distinct GCM ciphertexts $$(c_0, t_0)$$ and $$(c_1, t_1)$$,
   both encrypted with the _same secret key_ and
   the _same 96-bit encryption nonce_ $$\mathcal{N}$$.
   Show how the attacker can recover the GHASH key
   $$k_\text{m}$$ from these two ciphertext pairs.

   _Hint:_ The function GHASH is defined using arithmetic
   in $$GF(2^{128})$$, but you can think of GHASH
   as using arithmetic modulo a 128-bit prime $$p$$.
   In this setting, all of the "nice" algebraic properties hold:
   a polynomial of degree $$d < p$$ has at most $$d$$ distinct roots
   (and there is an efficient algorithm to find them),
   every element has an additive and multiplicative inverse, etc.

1. Propose one way to modify AES-GCM so that this
   integrity attack is not possible, even if the sender reuses
   the nonce.
   In one sentence, speculate on why the GCM designers did not incorporate
   your fix into their design.
