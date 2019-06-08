#!/usr/bin/env python

"""shors.py: Shor's algorithm for quantum integer factorization"""

import math
import random
import argparse
from pyquil.quil import Program
from pyquil.api import QVMConnection
from pyquil.gates import X, I
import numpy as np

from period import PERIOD

__author__ = "Todd Wildey"
__copyright__ = "Copyright 2013"
__credits__ = ["Todd Wildey"]

__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Todd Wildey"
__email__ = "toddwildey@gmail.com"
__status__ = "Prototype"

def printNone(str):
    pass

def printVerbose(str):
    print(str)

printInfo = printNone

####################################################################################################
#                                                                                                   
#                                        Quantum Components                                         
#                                                                                                   
####################################################################################################


def findPeriod(a, N):
    nNumBits = N.bit_length()
    inputNumBits = (2 * nNumBits) - 1
    inputNumBits += 1 if ((1 << inputNumBits) < (N * N)) else 0
    Q = 1 << inputNumBits

    printInfo("Finding the period...")
    printInfo("Q = " + str(Q) + "\ta = " + str(a))

    printInfo("Using {} bits".format(nNumBits))
    mine = PERIOD(a, N, nNumBits)
    printInfo("The x I found \tx = {:8b}".format(mine))
    r2 = cf(mine, Q, N)
    printInfo("My period\tr = {}".format(r2))
    return r2

####################################################################################################
#                                                                                                   
#                                       Classical Components                                        
#                                                                                                   
####################################################################################################

BIT_LIMIT = 12

def bitCount(x):
    sumBits = 0
    while x > 0:
        sumBits += x & 1
        x >>= 1

    return sumBits

# Greatest Common Divisor
def gcd(a, b):
    while b != 0:
        tA = a % b
        a = b
        b = tA

    return a

# Extended Euclidean
def extendedGCD(a, b):
    fractions = []
    while b != 0:
        fractions.append(a // b)
        tA = a % b
        a = b
        b = tA

    return fractions

# Continued Fractions
def cf(y, Q, N):
    fractions = extendedGCD(y, Q)
    depth = 2

    def partial(fractions, depth):
        c = 0
        r = 1

        for i in reversed(range(depth)):
            tR = fractions[i] * r + c
            c = r
            r = tR

        return c

    r = 0
    for d in range(depth, len(fractions) + 1):
        tR = partial(fractions, d)
        if tR == r or tR >= N:
            return r

        r = tR

    return r

# Modular Exponentiation
def modExp(a, exp, mod):
    fx = 1
    while exp > 0:
        if (exp & 1) == 1:
            fx = fx * a % mod
        a = (a * a) % mod
        exp = exp >> 1

    return fx

def pick(N):
    a = math.floor((random.random() * (N - 1)) + 0.5)
    return a

def checkCandidates(a, r, N, neighborhood):
    if r is None:
        return None

    # Check multiples
    for k in range(1, neighborhood + 2):
        tR = k * r
        if modExp(a, a, N) == modExp(a, a + tR, N):
            return tR

    # Check lower neighborhood
    for tR in range(r - neighborhood, r):
        if modExp(a, a, N) == modExp(a, a + tR, N):
            return tR

    # Check upper neigborhood
    for tR in range(r + 1, r + neighborhood + 1):
        if modExp(a, a, N) == modExp(a, a + tR, N):
            return tR

    return None

def shors(N, attempts = 1, neighborhood = 0.0, numPeriods = 1):
    if(N.bit_length() > BIT_LIMIT or N < 3):
        return False

    periods = []
    neighborhood = math.floor(N * neighborhood) + 1

    printInfo("N = " + str(N))
    printInfo("Neighborhood = " + str(neighborhood))
    printInfo("Number of periods = " + str(numPeriods))

    for attempt in range(attempts):
        printInfo("\nAttempt #" + str(attempt))

        a = pick(N)
        while a < 2:
            a = pick(N)

        d = gcd(a, N)
        if d > 1:
            printInfo("Found factors classically, re-attempt")
            continue

        r = findPeriod(a, N)

        printInfo("Checking candidate period, nearby values, and multiples")

        r = checkCandidates(a, r, N, neighborhood)

        if r is None:
            printInfo("Period was not found, re-attempt")
            continue

        if (r % 2) > 0:
            printInfo("Period was odd, re-attempt")
            continue

        d = modExp(a, (r // 2), N)
        if r == 0 or d == (N - 1):
            printInfo("Period was trivial, re-attempt")
            continue

        printInfo("Period found\tr = " + str(r))

        periods.append(r)
        if(len(periods) < numPeriods):
            continue

        printInfo("\nFinding least common multiple of all periods")

        r = 1
        for period in periods:
            d = gcd(period, r)
            r = (r * period) // d

        b = modExp(a, (r // 2), N)
        f1 = gcd(N, b + 1)
        f2 = gcd(N, b - 1)

        return [f1, f2]

    return None

####################################################################################################
#                                                                                                   
#                                    Command-line functionality                                     
#                                                                                                   
####################################################################################################

def parseArgs():
    parser = argparse.ArgumentParser(description='Simulate Shor\'s algorithm for N.')
    parser.add_argument('-a', '--attempts', type=int, default=20, help='Number of quantum attemtps to perform')
    parser.add_argument('-n', '--neighborhood', type=float, default=0.01, help='Neighborhood size for checking candidates (as percentage of N)')
    parser.add_argument('-p', '--periods', type=int, default=2, help='Number of periods to get before determining least common multiple')
    parser.add_argument('-v', '--verbose', type=bool, default=True, help='Verbose')
    parser.add_argument('N', type=int, help='The integer to factor')
    return parser.parse_args()

def main():
    args = parseArgs()

    global printInfo
    if args.verbose:
        printInfo = printVerbose
    else:
        printInfo = printNone

    factors = shors(args.N, args.attempts, args.neighborhood, args.periods)
    if factors is not None:
        print("Factors:\t" + str(factors[0]) + ", " + str(factors[1]))

if __name__ == "__main__":
    main()
