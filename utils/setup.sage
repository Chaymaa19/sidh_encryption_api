#!/usr/bin/env sage

import common

def generate_keys(my_l, my_e, my_p, my_q, other_p, other_q ):
    m, n = randint(0,my_l**my_e-1), randint(0,my_l**my_e-1)
    subgroup = m * my_p + n *my_q
    phi = common.E.isogeny(subgroup, algorithm="factored")
    my_E = phi.codomain()

    return m, n, my_E, phi(other_p), phi(other_q)

# Generate receiver credentials
ma, na, Ea, phi_a_pb, phi_a_qb = generate_keys(2, common.ea, common.pa, common.qa, common.pb, common.qb)
print(f"{ma}_{na}_{Ea.ainvs()}_{phi_a_pb}_{phi_a_qb}")

# Generate sender credentials
mb, nb, Eb, phi_b_pa, phi_b_qa = generate_keys(3, common.eb, common.pb, common.qb, common.pa, common.qa)
print(f"{mb}_{nb}_{Eb.ainvs()}_{phi_b_pa}_{phi_b_qa}")