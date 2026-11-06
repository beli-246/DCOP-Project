"""Choosing which k departments lie, and with which attacks."""
import random


def pilot_liars(inst, k, seed):
    """Exactly the pilot's choice: random.Random(2000 + seed).sample(range(N), k)."""
    return set(random.Random(2000 + seed).sample(range(inst['N']), k))


def place_liars(inst, k, placement='random', seed=0):
    """Pick k departments.

    random:   uniform sample.
    adjacent: grown from a random department by breadth-first search over the neighbour
              graph, so liars share students with each other where possible.
    spread:   greedy, each new liar chosen to have as few liar neighbours as possible
              (an independent set when one of size k exists).
    """
    N, nbr = inst['N'], inst['nbr']
    if not 0 <= k <= N:
        raise ValueError(f'k={k} not in [0, {N}]')
    rng = random.Random(3000 + seed)
    if k == 0:
        return set()
    if placement == 'random':
        return set(rng.sample(range(N), k))
    if placement == 'adjacent':
        order = list(range(N))
        rng.shuffle(order)
        chosen, queue = [], [order[0]]
        seen = {order[0]}
        while len(chosen) < k:
            if not queue:                      # neighbour graph disconnected: jump to a new start
                nxt = next(i for i in order if i not in seen)
                seen.add(nxt)
                queue.append(nxt)
            i = queue.pop(0)
            chosen.append(i)
            nb = sorted(nbr[i] - seen)
            rng.shuffle(nb)
            for j in nb:
                seen.add(j)
                queue.append(j)
        return set(chosen)
    if placement == 'spread':
        chosen = set()
        cand = list(range(N))
        rng.shuffle(cand)
        for _ in range(k):
            best = min((i for i in cand if i not in chosen), key=lambda i: len(nbr[i] & chosen))
            chosen.add(best)
        return chosen
    raise ValueError(placement)


def make_types(inst, liars, attacks):
    """types list: 'honest' for everyone not in liars; liars get attacks.

    attacks: one attack name (all liars use it) or a list cycled over the liars in sorted order
    (mixed attacks).
    """
    types = ['honest'] * inst['N']
    if isinstance(attacks, str):
        attacks = [attacks]
    for n, i in enumerate(sorted(liars)):
        types[i] = attacks[n % len(attacks)]
    return types


def liar_adjacency(inst, liars):
    """Number of liar-liar neighbour pairs (0 for a spread placement, high for adjacent)."""
    L = sorted(liars)
    return sum(1 for a in range(len(L)) for b in range(a + 1, len(L)) if L[b] in inst['nbr'][L[a]])
