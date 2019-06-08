from final2 import phase_helper
from IPython import embed

import pickle

#import matplotlib
#import matplotlib.pyplot as plt

def main():
    primes = [5,7,11,13,17,19]
    muls = [x*y for x in primes for y in primes]
    muls = list(set(muls))
    muls.sort()
    bits = [x.bit_length() for x in muls]
    gates = []
    qubits = []
    f = open("jar/gates.pickle", "bw")
    for i, x in enumerate(muls):
        print("{} : {} bits".format(x, bits[i]))
        p = phase_helper(3, x, bits[i])
        num_gates = len(p.instructions)
        num_qubits = len(p.get_qubits())
        gates.append(num_gates)
        qubits.append(num_qubits)
        print("{} gates".format(num_gates))
        print("{} qubits".format(num_qubits))
    pickle.dump((muls, bits, gates, qubits), f)
    embed(colors="Neutral")


if __name__ == "__main__":
    main()
