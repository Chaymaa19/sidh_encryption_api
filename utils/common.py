#!/usr/bin/env python
import os

from sage.all import *

# Fixed parameters
ea = int(os.getenv('ea'))
eb = int(os.getenv('eb'))
p = 2 ** ea * 3 ** eb - 1
# Start by using the curve y^2 = x^3 + x
E = EllipticCurve(GF(p ** 2, 'a'), [0, 0, 0, 1, 0])
g1, g2 = E.gens()

# Get Alice's points
pa = 3 ** eb * g1
qa = 3 ** eb * g2

# Get Bob's points
pb = 2 ** ea * g1
qb = 2 ** ea * g2
