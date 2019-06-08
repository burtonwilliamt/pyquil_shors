from typing import List
import numpy as np

import math

from IPython import embed

from pyquil.quil import Program, address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.api import QVMConnection
from pyquil.gates import X, I, H, CNOT, CCNOT, MEASURE

qvm = QVMConnection()

#NOTE: This code is inneficient, and now depreciated in preference of the code found in 
def REVERSE(p):
    rev_p = p.copy_everything_except_instructions()
    rev_p += Program(f"#BEGIN REVERSE:")
    for inst in reversed(p.instructions):
        rev_p += inst
    return rev_p

def CARRY(c_in, a, b, c_out):
        p = Program(f"#CARRY {c_in} {a} {b} {c_out}")
        p += CCNOT(a,b,c_out)
        p += CNOT(a,b)
        p += CCNOT(c_in,b,c_out)
        p += Program(f"#END CARRY {c_in} {a} {b} {c_out}")
        return p

def SUM(c_in, a, b, c_out=None):
    p = Program(f"#SUM {c_in} {a} {b}")
    p += CNOT(a, b)
    p += CNOT(c_in, b)
    p += Program(f"#END SUM {c_in} {a} {b}")
    return p

def ADDER(carry_r, a_r, b_r):
    #assert len(carry_r) == len(a_r) == len(b_r)-1
    #carry_r = QubitPlaceholder.register(len(a_r))
    p = Program(f"#ADDER")
    n = len(b_r)-1
    args_sets = []
    for i in range(n):
        c_in = carry_r[i]
        a = a_r[i]
        b = b_r[i]
        c_out = None
        if i == n-1:
            c_out = b_r[i+1]
        else:
            c_out = carry_r[i+1]
        args_sets.append((c_in, a, b, c_out))
    for args in args_sets:
        p += CARRY(*args)

    p += CNOT(a_r[n-1], b_r[n-1])
    p += SUM(*args_sets[-1])
    for args in reversed(args_sets[:-1]):
        p += REVERSE(CARRY(*args))
        p += SUM(*args)
    p += Program(f"#END ADDER")
    return p


#p += write_in(N, N_r)
def ADDER_MOD(carry_r, a_r, b_r, N_r, N, t):
    p = Program(f"#ADDER MOD {N}")
    p += ADDER(carry_r, a_r, b_r)
    #How many multiples do we want to be safe from?
    #If a+b = k*N then we need k times the below block
    #To be safe, we should do floor( ( (1 << len(a_r) - 1) + (1 << len(b_r) -1) )/N )
    #saftey = math.floor( ( (1 << len(a_r)) - 1 + (1 << len(b_r)) -1)/float(N) )
    #print("Saftey is "+str(saftey))
    #for _ in range(saftey):
    p += REVERSE(ADDER(carry_r, N_r, b_r))
    p += X(b_r[-1])
    p += CNOT(b_r[-1], t)
    p += X(b_r[-1])
    p += CTRL_NUM(t, N_r, N)
    p += ADDER(carry_r, N_r, b_r)
    p += CTRL_NUM(t, N_r, N)
    p += REVERSE(ADDER(carry_r, a_r, b_r))
    p += CNOT(b_r[-1], t)
    p += ADDER(carry_r, a_r, b_r)

    return p


def MUL_MOD(carry_r, a_r, b_r, N_r, N, t, nila, mult, ctrl):
    p = Program()
    for i in range(len(a_r)):
        p += CCTRL_NUM(ctrl, a_r[i], nila, mult*(2**i)%N)
        p += ADDER_MOD(carry_r, nila, b_r, N_r, N, t)
        p += CCTRL_NUM(ctrl, a_r[i], nila, mult*(2**i)%N)

    p += X(ctrl)
    for i in range(len(a_r)):
        p += CCNOT(ctrl, a_r[i], b_r[i])
    p += X(ctrl)
    return p

def EXP_MOD(carry_r, a_r, b_r, N_r, N, t, nila, base, exp):
    # a starts at 1, b starts at 0
    p = Program()
    for i in range(len(exp)):
        p += MUL_MOD(carry_r, a_r, b_r, N_r, N, t, nila, base**(2**i), exp[i])
        p += REVERSE(MUL_MOD(carry_r, b_r, a_r, N_r, N, t, nila, base**(2**i), exp[i]))
    return p


def CCTRL_NUM(ctrl1, ctrl2, reg, val):
    p = Program()

    bitstring = str(bin(val))[2:]
    bitstring = "0"*(len(reg)-len(bitstring)) + bitstring

    for idx, bit in enumerate(reversed(list(bitstring))):
        if bit == '1':
            p += CCNOT(ctrl1, ctrl2, reg[idx])

    return p

#This takes zero to some value or that value back to zero
def CTRL_NUM(ctrl, reg, val):
    p = Program()

    bitstring = str(bin(val))[2:]
    bitstring = "0"*(len(reg)-len(bitstring)) + bitstring

    for idx, bit in enumerate(reversed(list(bitstring))):
        if bit == '1':
            p += CNOT(ctrl, reg[idx])

    return p

def SUPERPOS(reg):
    p = Program()
    for qbit in reg:
        p += H(qbit)
    return p

def write_in(val, reg):
    p = Program()

    bitstring = str(bin(val))[2:]
    bitstring = "0"*(len(reg)-len(bitstring)) + bitstring

    for idx, bit in enumerate(reversed(list(bitstring))):
        if bit == "1":
            p += X(reg[idx])

    return p

def read_out(p, reg):

    p = Program(p)
    ro = p.declare('ro', 'BIT', len(reg))

    for i in range(len(reg)):
        p += MEASURE(reg[i], ro[i])

    p = address_qubits(p)
    result = qvm.run(p)

    outp = 0
    for i in range(len(result[0])):
        if(result[0][i] == 1):
            outp += 2**i
    return (outp, p)


def lookup_append(qbit_lookup, reg, name):
    for i in range(len(reg)):
        qbit_id = repr(reg[i]).split()[1][:-1]
        qbit_lookup[qbit_id] = "{}_{}".format(name, i)

def pretty_print(qbit_lookup):
    pp = ""
    for line in str(Program(ADDER(c,a,b))).splitlines():
        for item in line.split():
            check = item[2:][:-1]
            if check.isdigit():
                item = qbit_lookup[check]
            pp += item+" "
        pp += "\n"

    print(pp)


def main():

    A_SIZE = 4
    a = QubitPlaceholder.register(A_SIZE)
    n = QubitPlaceholder.register(A_SIZE)
    b = QubitPlaceholder.register(A_SIZE)
    c = QubitPlaceholder.register(A_SIZE)
    exp = QubitPlaceholder.register(A_SIZE)
    t = QubitPlaceholder()

    nila = QubitPlaceholder.register(A_SIZE)

    master = QubitPlaceholder()

    N = 3
    base = 2

    p = Program()

    p += write_in(1, exp)
    p += write_in(1, a)
    p += write_in(0, b)
    p += write_in(N, n)
    p += write_in(0, c)


    p += EXP_MOD(c, a, b, n, N, t, nila, base, exp)
    #p += MUL_MOD(c, a, b, n, N, t, nila, multiplier, master)
    #p += ADDER_MOD(c, a, b, n, N, t)
    #p += REVERSE(ADDER(c, a, b))
    #p += ADDER(c, a, b)

    res, code = read_out(p, a)
    print(res)

    #qbit_lookup = {}
    #lookup_append(qbit_lookup, a, "a")
    #lookup_append(qbit_lookup, b, "b")
    #lookup_append(qbit_lookup, c, "c")
    #pretty_print(qbit_lookup)

    embed(colors="Neutral")


if __name__ == "__main__":
    main()
