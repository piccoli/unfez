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

import os, sys, re, operator, cairo

from functools import reduce
from PIL       import Image
from unfez     import log

DATAP = 'data'
SYMF  = os.path.join(DATAP, 'sym.png'  )
SYMIF = os.path.join(DATAP, 'sym.index')
TS    = 18
MAXD  = 1.

def main():
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        log('Usage: {} <image file>.'.format(sys.argv[0]))
        sys.exit(1)

    try:
        img  = Image.open(sys.argv[1])
    except IOError as e:
        log(e)
        sys.exit(1)

    prepare(img)
    get_letters( img.crop( get_roi( *get_bb( *img.size ) )[1] ) )

def prepare(img):
    global CSum
    CSum = []
    data = img.getdata()
    w, h = img.size
    for j in range(w):
        CSum.append([ 0 ])
        for i in range(h):
            d = data[i * w + j]
            if d[0] == d[1] == d[2]:
                d = 255 - d[0]
            else:
                d = -grayscale(d)
            CSum[j].append(CSum[j][i] + d)

def grayscale(c):
    return c[0] if reduce(operator.eq, c) else round(.299 * c[0] + .587 * c[1] + .114 * c[2])

def get_roi(a, b, c, d, M = {}):
    key = (a, b, c, d)
    if key in M:
        return M[key]
    if a == b:
        M[key] = maxsum(a, a, c, d)
        return M[key]
    m = a + ((b - a) >> 1)
    ra = get_roi(a    , m, c, d, M)
    rb = get_roi(m + 1, b, c, d, M)
    if ra[0] == 0:
        M[key] = rb
        return M[key]
    if rb[0] == 0:
        M[key] = ra
        return M[key]
    M[key] = max(maxsum (a    , b    , c, d   ),\
                 get_roi(a + 1, b    , c, d, M),\
                 get_roi(a    , b - 1, c, d, M))
    return M[key]

def maxsum(a, b, c, d):
    l = c
    maxhere = 0
    maxs, roi = 0, (c, a, d, b)
    for j in range(c, d + 1):
        s = maxhere + csum(j, a, b)
        if s < 0:
            l = j + 1
            continue
        maxhere = max(0, s)
        if maxhere > maxs:
            maxs, roi = maxhere, (l, a, j, b)
    return maxs, roi

def csum(j, a, b):
    return CSum[j][b + 1] - CSum[j][a]

def get_letters(roi):
    tiles   = load_tiles()
    letters = []
    w, h    = roi.size
    d       = [ (255 - grayscale(c)) / 255. for c in roi.getdata() ]

    row_matched = False
    for i in skip_range(h, lambda: row_matched, 2):
        row_matched = False
        for j in skip_range(w, lambda: col_matched):
            col_matched = False
            a = match_tile(d, tiles, i, j, w)
            if a == -1:
                continue
            letters.append((a, (w - j - TS) * h + i, j, i))
            if a < len(tiles) - 1:
                row_matched = col_matched = True

    letters.sort(key = lambda x: x[1])
    render(letters, tiles)

    words = [ w.strip()
                for w in ' '
                         .join(
                             str(l[0])
                                 for l in letters
                         )
                         .split(
                             str(len(tiles) - 1)
                         )
            ]
    for wd in filter(len, words):
        print(wd)
    print(-1)

def skip_range(x, matchfun, align = 0):
    i = 0
    while i <= x - TS:
        yield i
        i += TS + align + 1 if matchfun() else 1

def load_tiles():
    try:
        sym = Image.open(SYMF)
        with open(SYMIF) as f:
            nsym = [ int(x) for x in f.readline().split() ]
    except IOError as e:
        log(e)
        sys.exit(1)

    tiles = [ [] for _ in range(len(nsym)) ]
    y = 0
    for i, c in enumerate(nsym):
        x = 0
        for j in range(c):
            t = sym.crop((x, y, x + TS, y + TS))
            tiles[i].append([ d / 255. for d in t.getdata() ])
            x += TS
        y += TS
    return tiles

def match_tile(d, tiles, i, j, w):
    mina, mins = -1, MAXD
    def check_tile(t):
        nonlocal a, mina, mins
        kl = s = 0
        for k in range(TS):
            for l in range(TS):
                s += (t[kl] - d[(i + k) * w + j + l]) ** 2
                if s >= mins:
                    return
                kl += 1
        mina, mins = a, s

    for a, tl in enumerate(tiles):
        for t in tl:
            check_tile(t)
    return mina

def get_bb(w, h):
    a, b, c, d = h, 0, w, 0
    for j in range(w):
        for i in range(h):
            if csum(j, i, i) > 0:
                a = min(a, i)
                b = max(b, i)
                c = min(c, j)
                d = max(d, j)
    return a, b, c, d

def render(letters, tiles):
    SEP = 1
    x0  = min(l[2] for l in letters if l[0] != len(tiles) - 1)
    y0  = min(l[3] for l in letters if l[0] != len(tiles) - 1)
    w   = max(l[2] for l in letters if l[0] != len(tiles) - 1) + TS - x0 + 2 * SEP
    h   = max(l[3] for l in letters if l[0] != len(tiles) - 1) + TS - y0 + 2 * SEP
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr  = cairo.Context(out)

    for l in letters:
        i    = l[0]
        x, y = l[2] - x0 + SEP, l[3] - y0 + SEP
        tile = cairo.ImageSurface.create_from_png(os.path.join(DATAP, 'avg', '{}.png'.format(i)))
        cr.set_source_surface(tile, x, y)
        cr.paint()
        tile.finish()
    out.write_to_png(re.sub(r'^([^\.]*)(\.[^\.]+)?$', r'\1_in.png', sys.argv[1]))

if __name__ == '__main__':
    main()
