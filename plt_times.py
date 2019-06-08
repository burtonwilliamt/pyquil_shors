from IPython import embed
import pickle
import matplotlib
import matplotlib.pyplot as plt

import numpy as np

def main():
    f = open("jar/gates.pickle", "br")
    muls, bits, gates, qubits = pickle.load(f)
    fig = plt.figure()
    plt.gcf().subplots_adjust(left=0.15)
    ax = plt.subplot(111)
    log_size = [ np.log(x)/np.log(2) for x in muls ]
    ax.set_xlabel("Log size of N")
    ax.set_ylabel("Number of gates")
    ax.plot(log_size, gates, 'r')
    fig.savefig('gates.png')
    plt.close(fig)

    fig = plt.figure()
    plt.gcf().subplots_adjust(left=0.15)
    ax = plt.subplot(111)
    ax.set_xlabel("Log size of N")
    ax.set_ylabel("Number of qubits")
    ax.plot(log_size, qubits, 'r')
    fig.savefig('qubits.png')
    plt.close(fig)
    embed(colors="Neutral")


if __name__ == "__main__":
    main()
