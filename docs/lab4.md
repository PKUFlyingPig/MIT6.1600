---
title: "Lab 4: Isolation"
---

In this lab assignment, you will attack various not-quite-secure ways
of isolating code.

## Problem 1: Python

Python does not provide isolation, so in this assignment,
your job is to demonstrate this in several different
scenarios.  Specifically, the grader for this problem,
[`grader.py`](https://github.com/mit-pdos/6.1600-labs/tree/main/escape/grader.py),
chooses a random value `secret`, and calls one of your attack functions,
`attack_one()` through `attack_four()`, that you will need to implement in
[`attack.py`](https://github.com/mit-pdos/6.1600-labs/tree/main/escape/attack.py).
Your attack function must figure out the correct secret value and
return it.

Solve the four attack puzzles.  You can do anything you want in `attack.py`,
but you may not modify `grader.py`.  This problem will require you to
understand what is shared between your function's execution environment and
the secret chosen by the grader scenario code, and take advantage of it.
There are many ways to solve each scenario.  Some solutions could work
for multiple scenarios.  There are more than 4 substantially different
ways to solve the scenarios, though, so try to find distinct solutions.

## Problem 2: Web Assembly

(Copy over from last year)
