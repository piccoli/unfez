#! /usr/bin/python3 -O
# -*- coding: utf-8 -*-
## Copyright (C) 2014 Ricardo Piccoli <rfbpiccoli@gmail.com>
##
## This file is free software; as a special exception the author gives
## unlimited permission to copy and/or distribute it, with or without
## modifications, as long as this notice is preserved.
##
## This program is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY, to the extent permitted by law; without even the
## implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

__all__ = []

import sys, glob, operator, random, os
from PIL       import Image
from functools import reduce, lru_cache

SEED     = 12345
K        = 24
RESTARTS = 2
MAXINT   = (1 << 31) - 1

class Cluster:
    def __init__(self, m, xt1 = [], xt = None):
        assert type(xt1) is list
        assert type(xt) is None or type(xt) is list
        self.m   = m
        self.xt1 = list(xt1)
        self.xt  = None if xt is None else list(xt)
    def rotate(self):
        self.xt = list(self.xt1)
        self.xt1.clear()
    def changed(self):
        return self.xt1 != self.xt

def main():
    try:
        imgs = [ Image.open(f) for f in glob.glob('*_*.png') ]
    except IOError as e:
        print(e, file = sys.stderr)
        sys.exit(1)

    assert reduce(operator.eq, (im.size for im in imgs))
    n = reduce(operator.mul, imgs[0].size)

    x = [ im.getdata() for im in imgs ]
    assert all(filter(lambda c: type(c[0]) is int, x))

    s = [ Cluster(None) for k in range(K) ]
    minw, minm = MAXINT, None
    #random.seed(SEED)
    random.seed()
    for i in range(RESTARTS):
        print('Run #{}'.format(i), file = sys.stderr)
        init(s, x)
        while assign(s, x):
            update(s, x, n)
        r = sum(sum(dist(tuple(k.m), tuple(x[j])) for j in k.xt1) for k in s)
        if r < minw:
            minw, minm = r, [ Cluster(k.m, k.xt1, k.xt) for k in s ]

    for i, k in enumerate(minm):
        os.makedirs(str(i), mode = 0o750, exist_ok = True)
        for j in k.xt1:
            os.rename(imgs[j].filename, os.path.join(str(i), imgs[j].filename))

def init(s, x):
    l = list(range(len(x)))
    for k in s:
        i = random.randint(0, len(l) - 1)
        l[-1], l[i] = l[i], l[-1]
        k.m = list(x[l.pop()])

def assign(s, x):
    for k in s:
        k.rotate()
    for i, xi in enumerate(x):
        minm, mink = MAXINT, None
        for k in s:
            d = dist(tuple(xi), tuple(k.m))
            if d < minm:
                minm, mink = d, k
        mink.xt1.append(i)
    for k in s:
        if k.changed():
            return True
    return False

def update(s, x, n):
    for k in s:
        if len(k.xt1) == 0:
            k.m = [ MAXINT for i in range(n) ]
            continue
        #k.m = [ sum(x[j][i] for j in k.xt1) / len(k.xt1) for i in range(n) ]
        k.m = [ reduce(operator.mul, (x[j][i] for j in k.xt1)) ** (1. / len(k.xt1)) for i in range(n) ]

@lru_cache(maxsize = 1 << 16)
def dist(a: tuple, b: tuple):
    return sum((a[i] - b[i]) ** 2 for i in range(len(a)))

if __name__ == '__main__':
    main()
