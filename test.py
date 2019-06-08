from period import *

def test_adder(size):
    print("Starting the adder test for numbers of size {}".format(size))
    b = QubitPlaceholder.register(size+1)
    c1 = QubitPlaceholder()
    c2 = QubitPlaceholder()
    all_passed = True
    for i in range(2**size):
        for j in range(2**size):
            p = Program()
            p += get_defs()
            p += write_in(i, b)

            p += X(c1)
            p += X(c2)
            p += QFT(b)
            p += CCPSIADDER(c1, c2, b, j)
            p += REVERSE(QFT(b))

            outp, prog = read_out(p, b)
            res = i+j == outp
            if not res:
                print("-"*10)
                print("b = {:4b}\na = {:4b}\n+ = {:4b} ({})".format(i, j, outp, res))
                all_passed = False
    if not all_passed:
        print("Uh-oh, there were errors")
    else:
        print("Success, all tests passed")

def test_mod_adder(size):
    print("Starting the adder test for numbers of size {}".format(size))
    b = QubitPlaceholder.register(size+1)
    c1 = QubitPlaceholder()
    c2 = QubitPlaceholder()
    zero = QubitPlaceholder()
    all_passed = True
    for N in range(0, 2**size):
        for i in range(0, N):
            for j in range(0, N):
                p = Program()
                p += get_defs()
                p += write_in(i, b)

                p += X(c1)
                p += X(c2)
                p += QFT(b)
                p += PSIADDERMOD(c1, c2, b, j, N, zero)
                p += REVERSE(QFT(b))

                outp, prog = read_out(p, b)
                expected = (i+j)%N
                res = expected == outp
                if not res:
                    print("-"*10)
                    print("b = {:8b}\na = {:8b}\nN = {:8b}\n+ = {:8b} != {:8f} ({})".format(i, j, N, outp, expected, res))
                    all_passed = False
    if not all_passed:
        print("Uh-oh, there were errors")
    else:
        print("Success, all tests passed")


def test_cmult(size):
    print("Starting the adder test for numbers of size {}".format(size))
    b = QubitPlaceholder.register(size+1)
    x = QubitPlaceholder.register(size)
    c1 = QubitPlaceholder()
    zero = QubitPlaceholder()
    all_passed = True
    for N in range(0, 2**size):
        for i in range(0, N):
            for j in range(0, 2**size):
                for k in range(0, 2**size):
                    p = Program()
                    p += get_defs()

                    p += write_in(i, b)
                    p += write_in(k, x)

                    p += X(c1)
                    # this takes x, b to x, b + a*x mod N
                    p += CMULTMOD(c1, x, b, j, N, zero)

                    outp, prog = read_out(p, b)
                    expected = (i+j*k)%N
                    res = expected == outp
                    if not res:
                        print("-"*10)
                        print("b = {:8b}\na = {:8b}\nN = {:8b}\n+ = {:8b} != {:8f} ({})".format(i, j, N, outp, expected, res))
                        all_passed = False
    if not all_passed:
        print("Uh-oh, there were errors")
    else:
        print("Success, all tests passed")

def test_ua(size):
    print("Starting the UA test for numbers of size {}".format(size))
    zeros = QubitPlaceholder.register(size+1)
    x = QubitPlaceholder.register(size)
    c1 = QubitPlaceholder()
    zero = QubitPlaceholder()
    all_passed = True
    for N in range(1, 2**size):
        for j in range(0, 2**size):
            for k in range(0, 2**size):
                g, _, _ = egcd(j, N)
                if g != 1 :
                    continue
                #assert (modinv(j, N)*j)%N == 1
                p = Program()
                p += get_defs()

                p += write_in(k, x)

                p += X(c1)
                # this takes x, to a*x mod N
                p += UA(c1, x, zeros, j, N, zero)

                outp, prog = read_out(p, x)
                expected = (j*k)%N
                res = expected == outp
                if not res:
                    print("-"*10)
                    print("a = {:8b}\nx = {:8b}\nN = {:8b}\n* = {:8b} != {:8f} ({})".format(j, k, N, outp, expected, res))
                    all_passed = False
    if not all_passed:
        print("Uh-oh, there were errors")
    else:
        print("Success, all tests passed")

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

def main():
    test_adder(4)

if __name__=="__main__":
    main()
