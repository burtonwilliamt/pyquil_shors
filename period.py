import numpy as np

import math

from pyquil.quil import Program, address_qubits
from pyquil.quilatom import QubitPlaceholder

from pyquil.api import QVMConnection
from pyquil.gates import X, I, H, CNOT, CCNOT, MEASURE, SWAP
from pyquil.parameters import Parameter, quil_exp
from pyquil.quilbase import DefGate

def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    else:
        return x % m

qvm = QVMConnection()

k = Parameter('k')
ccrk = np.array([
    [1, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, quil_exp(  (2*np.pi*1j)/( 2**k )  )],
    ])
ccrk_gate_def = DefGate('CCRK', ccrk, [k])
CCRK = ccrk_gate_def.get_constructor()

crk = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, quil_exp(  (2*np.pi*1j)/( 2**k )  )],
    ])
crk_gate_def = DefGate('CRK', crk, [k])
CRK = crk_gate_def.get_constructor()

rk = np.array([
    [1, 0],
    [0, quil_exp(  (2*np.pi*1j)/( 2**k )  )],
    ])
rk_gate_def = DefGate('RK', rk, [k])
RK = rk_gate_def.get_constructor()


def get_defs():
    p = Program()
    p += ccrk_gate_def
    p += crk_gate_def
    p += rk_gate_def
    return p

def REVERSE(p):
    rev_p = p.copy_everything_except_instructions()
    rev_p += Program(f"#BEGIN REVERSE:")
    for inst in reversed(p.instructions):
        rev_p += inst.dagger()
    return rev_p

def CSWAP(c, l, r):
    p = Program()
    p += CNOT(r, l)
    p += CCNOT(c, l, r)
    p += CNOT(r, l)
    return p

def QFT(reg):
    p = Program()
    n = len(reg)
    for i in range(n-1, -1, -1):
        p += H(reg[i])
        for j in range(i-1, -1, -1):
            k = i-j+1
            p += CRK(k)(reg[j], reg[i])

    return p

def PSIADDER(b, a):
    # this is an adder in the fourier space
    # b is a register of size n+1 with value fit in n bits
    # a is a classicall number, must also fit in n bits
    assert(a < 2**(len(b)-1))
    p = Program()
    n = len(b)
    control = str(bin(a))[2:]
    control = list(reversed("0"*(len(b)-len(control)) + control))
    for i in range(n-1, -1, -1):
        #TODO: we can condense these j gates
        for j in range(i, -1, -1):
            if control[j] == "1":
                k = i-j+1
                p += RK(k)(b[i])
    return p

def CPSIADDER(c1, b, a):
    # this is an adder in the fourier space
    # b is a register of size n+1 with value fit in n bits
    # a is a classicall number, must also fit in n bits
    assert(a < 2**(len(b)-1))
    p = Program()
    n = len(b)
    control = str(bin(a))[2:]
    control = list(reversed("0"*(len(b)-len(control)) + control))
    for i in range(n-1, -1, -1):
        #TODO: we can condense these j gates
        for j in range(i, -1, -1):
            if control[j] == "1":
                k = i-j+1
                p += CRK(k)(c1, b[i])
    return p

def CCPSIADDER(c1, c2, b, a):
    # this is an adder in the fourier space
    # b is a register of size n+1 with value fit in n bits
    # a is a classicall number, must also fit in n bits
    assert(a < 2**(len(b)-1))
    p = Program()
    n = len(b)
    control = str(bin(a))[2:]
    control = list(reversed("0"*(len(b)-len(control)) + control))
    for i in range(n-1, -1, -1):
        #TODO: we can condense these j gates
        for j in range(i, -1, -1):
            if control[j] == "1":
                k = i-j+1
                p += CCRK(k)(c1, c2, b[i])
    return p


def PSIADDERMOD(c1, c2, b, a, N, zero):
    p = Program()
    # make b = b+a
    p += CCPSIADDER(c1, c2, b, a)
    # make b = b+a-N
    p += REVERSE(PSIADDER(b, N))

    # make zero now has ?(b+a < N)
    p += REVERSE(QFT(b))
    p += CNOT(b[-1] , zero)
    p += QFT(b)

    # if ?(b+a < N), add back N
    p += CPSIADDER(zero, b, N)
    # now b = b+a Mod N

    # Must get zero back to 0
    p += REVERSE(CCPSIADDER(c1, c2, b, a))
    p += REVERSE(QFT(b))
    p += X(b[-1])
    p += CNOT(b[-1] , zero)
    p += X(b[-1])
    p += QFT(b)
    p += CCPSIADDER(c1, c2, b, a)

    return p

def CMULTMOD(c1, x, b, a, N, zero):
    # takes in some x, b, outputs x, b + x*a mod N
    p = Program()
    p += QFT(b)
    for i in range(len(x)):
        p += PSIADDERMOD(c1, x[i], b, (a*(2**i))%N, N, zero)
    p += REVERSE(QFT(b))
    return p

def UA(c1, x, b, a, N, zero):
    p = Program()
    p += CMULTMOD(c1, x, b, a, N, zero)
    for i in range(len(x)):
        p += CSWAP(c1, x[i], b[i])
    ainv = modinv(a, N)
    ainv = ainv+abs(math.floor(ainv/N))*N
    p += REVERSE(CMULTMOD(c1, x, b, ainv, N, zero))
    return p

def period_helper(a, N, size):
    c1 = QubitPlaceholder()
    zero = QubitPlaceholder()
    x = QubitPlaceholder.register(size)
    b = QubitPlaceholder.register(size+1)
    #takes in x and b as zero, finds
    p = Program()

    n = 2*size
    def_regs = Program()
    period_regs = def_regs.declare('ro', 'BIT', n)

    #For one reg, we want H, CUA, R_i m_i, X^m_i
    for i in range(n-1, -1, -1):
        R = Program()
        R += H(c1)
        for j in range(i-1, -1, -1):
            k = i-j+1
            doit = Program()
            doit += RK(k)(c1).dagger()
            R = Program().if_then(period_regs[j], doit, I(c1)) + R
        R += MEASURE(c1, period_regs[i])
        R += Program().if_then(period_regs[i], X(c1), I(c1))
        #R = Program(H(c1)) + R
        R = Program(H(c1)) + UA(c1, x, b, a**(2**i), N, zero) + R
        p = R + p
    p = write_in(1, x) + p
    p = def_regs + p
    p = get_defs() + p
    p = address_qubits(p)
    return p

def PERIOD(a, N, size):
    p = period_helper(a, N, size)
    result = qvm.run(p)
    outp = 0
    for i in range(len(result[0])):
        if(list(reversed(result[0]))[i] == 1):
            outp += 2**i
    return outp

def PERIOD_slow(a, N, size):
    #NOTE: This code is accomplishes the same goal as PERIOD,
    #  but it does not use the single qubit input register trick.
    inp = QubitPlaceholder.register(2*size)
    zero = QubitPlaceholder()
    x = QubitPlaceholder.register(size)
    b = QubitPlaceholder.register(size+1)
    #takes in x and b as zero, finds
    p = Program()
    p += get_defs()
    p += write_in(1, x)
    for i in range(len(inp)):
        p += H(inp[i])
    for i in range(len(inp)):
        p += UA(inp[i], x, b, (a**(2**i)), N, zero)
    p += REVERSE(QFT(inp))
    print("Running a period finding alg using {} gates".format(len(p.instructions)))
    outp, p = read_out(p, list(reversed(inp)))
    return outp


def write_in(val, reg):
    p = Program()

    bitstring = str(bin(val))[2:]
    bitstring = "0"*(len(reg)-len(bitstring)) + bitstring

    for idx, bit in enumerate(reversed(list(bitstring))):
        if bit == "1":
            p += X(reg[idx])

    return p

def read_out(p, reg):

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


