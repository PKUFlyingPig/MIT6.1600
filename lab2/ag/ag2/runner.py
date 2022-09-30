from . import test_correctness
from . import test_malicious_client
from . import test_malicious_client_server
from ..ag1 import (
    basic_security as lab1_basic,
    fork_tests as lab1_fork,
)

# scale down all lab 1 test cases by a factor of 10
# skip hard-to-debug trace tests
from ..common.testing import scale_all_tests_in_module

scale_all_tests_in_module(lab1_basic, 2/12)
scale_all_tests_in_module(lab1_fork, 1/3)

