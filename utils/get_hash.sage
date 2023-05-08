#!/usr/bin/env sage

import common
import re

def get_hash(m, n, phi_p, phi_q, E):
    # Get Eab
    subgroup = m * phi_p + n * phi_q
    fi = E.isogeny(subgroup, algorithm="factored")
    Eba = fi.codomain()

    # Compute j(Eab)
    invariant = Eba.j_invariant()

    # Compute hash
    invariant = str(invariant)
    coeffs = re.findall(r'\d+', invariant)
    val = int(reduce((lambda x, y: int(x) * int(y)), coeffs))
    hash_val = str(bin(val))[2:]

    return hash_val


m = int(sys.argv[1])
n = int(sys.argv[2])
F.<a> = GF(common.p^2,'a')
curve = EllipticCurve(GF(common.p^2, 'a'), eval(sys.argv[3]))
phi_p = curve(eval(sys.argv[4]))
phi_q = curve(eval(sys.argv[5]))

hash_val = get_hash(m, n, phi_p, phi_q, curve)

print(hash_val)