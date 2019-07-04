import math

import matplotlib.pyplot as plt
import numpy as np


def gen_gbm(mu, sigma, n, t, s_0, seed):
    s = []
    np.random.seed(seed)
    w = [0]
    for i in range(1, n * t + 1):
        r = np.random.normal(0, 1)
        r /= math.sqrt(n)
        w.append(r + w[len(w) - 1])
    for i in range(0, n * t + 1):
        s.append(s_0 * math.exp(((mu - ((sigma ** 2) / 2)) * i / n) + sigma * w[i]))
    print(s)
    return s


gbm = gen_gbm(s_0=50, t=2, n=64, mu=.15, sigma=.4, seed=5)
plt.plot(gbm)
plt.show()
