---
title: "Lab 0: Password cracking"
---

<style type="text/css">
    ol { list-style-type: upper-alpha; }
</style>

<hr>

INSTRUCTIONS HERE ON HOW TO SUBMIT

INCLUDE DETAIL ON INSTANCE WE WILL RUN ON

<hr>

The [Boneh-Shoup book, Chapter 18.3](https://toc.cryptobook.us/book.pdf) is a good place to look if you would like to see a very detailed formal treatment of the ideas covered in this problem set.

You *MAY NOT* use any off-the-shelf password-cracking programs
or libraries to complete this problem.


# Problem 1: Storing passwords

Unix-like operating systems store password hashes in a file called `/etc/shadow`.
Answer the following questions:

1.  Typically, only the `root` user on a machine
has access to the `shadow` file. The `shadow` file
only contains passwords _hashes_ -- not the
passwords themselves. In one sentence, explain why
it is important to protect the hashed passwords.

1.  Look online for information about the `shadow`
file format. Why does the format allow the
password hashes for each user to be hashed with
a different hash function?

    _Learn about the PBKDF2 hash function by reading Chapter 18.4.3 of the [Boneh-Shoup book](https://toc.cryptobook.us/book.pdf). Then answer the following questions:_

1.  What security benefit does iterating a hash function provide?

1. Say that you are using PBKDF2 to protect passwords for authenticating
    to a popular web service (e.g., MIT Touchstone). How would you 
    set the iteration count?

1. If you were instead using PBKDF2 to protect
  passwords for authenticating to your laptop,
would your answer be the same or different as in
part (d)? Why?


# Problem 2: Cracking passwords

In reality, we use hash functions with 256 bits of
output, but in this problem we will work with
a toy hash function that has a 48-bit output.

For this problem, you will need to read through
the code at [hashall.py](lab0/hashall.py). 

That Python program reads each line from standard
input, hashes the resulting string using SHA256, 
and writes the first 48 bits of the hash to 
standard output as a hex string.


1. We ran the following code to hash the secret value `$PASSWORD` using the toy hash function defined in `hashall.py`:

    ```
    echo $PASSWORD | python hashall.py
    ```
    and it produced the output:
    ```
    a33a874eb313
    ```

    Write a program to find the value of `$PASSWORD`.
    Submit the password and your code.

    _Hint: `$PASSWORD` is a lower-case English word containing only the letters `a-z`._

1. If a user chooses a uniformly random string of 20 letters (`a-z`)
as their password, how many guesses on average
will it take to recover their password?

1. The file [hashes.txt](https://www.dropbox.com/s/jgfzvzs7xawx8kf/hashes.txt?dl=0) contains a large number of hashed passwords under the toy hash function defined in [hashall.py](lab0/hashall.py). These hashes are unsalted; we computed them exactly as we computed the hash in part (A). Write a program to find a preimage of one of the hashed passwords. Submit the preimage, its hash, and your code.

1. How would the cost of the preimage-finding attack change in part (C) if each hashed password were salted with a unique salt?


# Problem 3: Collisions

In this problem, we will explore the cost of
finding collisions in hash functions. The
"Birthday Paradox" analysis we cover here is one
of the most fundamental tools for reasoning about
the security of cryptosystems, so it's important
to understand.

Consider throwing $$B$$ balls into $$N$$ bins
at random. That is, for each ball, 
we pick a bin in $$\{1, \dots, N\}$$
independently and uniformly at random, and toss
the ball into that bin.

1. For a particular ball $$i$$ and bin $$k$$, what
   is the probability, as a function of $$B$$ and
   $$N$$, that ball $$i$$ falls into bin $$k$$?

1. For particular distinct balls $$i$$ and $$j$$, 
and for a particular bin $$k$$, what is the 
    probability, as a function of $$B$$ and $$N$$,
    that ball $$i$$ _and_ ball $$j$$ fall into bin
$$k$$?

1.  How many _pairs_ of distinct balls $$(i,j)$$ are there in
    total, as a function of $$B$$? 
    For example, if there were three balls 
    $$(B=3)$$ there would be a total of three pairs:
    $$(1, 2), (1, 3), (2, 3)$$.

1.  Give a non-trivial _upper bound_, as a function of $$B$$
    and $$N$$ on the probability that any two balls fall into the same bin.
    In other words, you will compute and
expression of the form $$\Pr[\text{two balls in same bin}] \leq \text{???}$$.
    
    _Hint: Use the union bound. That is, if
$$B_1$$ and $$B_2$$ are two bad events, then the
probability that either bad event occurs is at most
the sum of $$\Pr[B_1]$$ and $$\Pr[B_2]$$,
even if the events are dependent.
That is: $$\Pr[B_1 \lor B_2] \leq \Pr[B_1] + \Pr[B_2]$$._
   
1.  Let $$H \colon \{0,1\}^n \to \{0,1\}^n$$ be
    a random function. That is, for all $$x \in
\{0,1\}^n$$, the value $$H(x)$$ is a random
$$n$$-bit string chosen independent and uniformly
at random.

    Using your answer to part (D), compute give
    a non-trivial upper bound on the probability
    that there is a collision among $$H(x_1), H(x_2), \dots, H(x_L)$$,
    where $$x_1, \dots, x_L$$ are distinct $$n$$-bit
    strings with $$L \ll 2^n$$.


# Problem 4: Finding collisions

Let $$H$$ be the hash function defined in
[hashbig.py](lab0/hashbig.py).
This hash function has a 56-bit output and is
_NOT_ the same hash function as in Problem 2.

1. If you iterate the function $$H$$ on itself:

    $$H(x), H(H(x)), H(H(H(x))), \dots$$,

   eventually you will enter a cycle of repeating values. 
    Explain how to use such a cycle to find a collision in $$H$$
    (with high probability).

1. Write a program to find a collision in $$H$$.
   *Your program should complete in fewer than
   15 minutes on a modern laptop.*

   _Hint:_ Use your answer from Part (A).

   _Hint:_ For your program to run quickly, it should
    make as few memory accesses as possible.
    Making many lookups into a gigantic array 
    or hash table will slow you down.

    _Hint:_ For debugging, run your program on
    a small-output hash function first to make sure
    that it can actually find collisions.

