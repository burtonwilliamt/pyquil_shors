# pyquil_shors
An implementation of the Shor algorithm for factoring products of primes using the Quil instruction set.

## Description
This is my implementation of the algorithm first described by Peter Shor for factoring numbers in polinomial time. This particular implementation follows more closely with the paper by Stephane Beauregard that allows factoring to be done using only 2n+3 qubits. Much of the classical logic was borrowed from [another implementation](https://github.com/toddwildey/shors-python) of shors algorithm by toddwildey. However their implementation had a custom QPU simulator that was unrealistic in the types of operations it allowed.

The interesting development here is that I have implemented this algorithm using the pyQuil framework, which would allow this to directly run this code on a QPU. Hopefully this might allow some analysis of what a real world implementation of shors algorithm would be able to do, how many gates it would take, etc.

## Running
To run the code, you need to have the Quil framework, and a QVM running. The main file is `shor.py` but all the Quantum logic is in `period.py`. To execute, just clone and run:
`python shor.py -v true -p 1 21`

## Example run:
![An example of factoring 21](ShorsFactoring.png?raw=true "Example factoring run")
