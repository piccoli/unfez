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

__all__ = [ 'log' ]

import os, sys, re, random, math, string, bz2, pickle, cairo

from collections import namedtuple

CORPUS_FILE = 'datasets/wiki.txt.bz2'
NGRAM_CACHE = 'ngram.pickle'
NGRAM_SIZE  = 4
WSEP        = '|'
SEED        = 130000
ALPHABET    = list(string.ascii_lowercase)
ADJUST      = 256
ITERATIONS  = 512
T           = lambda x: .9975 ** (x * 1.7e3)
K           = 20.
NZ          = 1e-1
DATAP       = os.path.join('data', 'avg')
PDFOUT      = 'fezetta.pdf'
MM          = 25.4 * .013837 # Base unit is points.

Layout = namedtuple('Layout', 'fontname fontsize pagewidth pageheight margins colwidth rowheight xtextsep ytextsep tilesize rows')

class State:
    def __init__(self, s = ALPHABET, e = None):

        if type(s) is not list:
            raise TypeError("'list' expected, but received a '{}' instead!".format(type(s)))

        if len(s) != 26 or not all(map(lambda x: type(x) is str and len(x) == 1, s)):
            raise ValueError('You must provide a list containing exactly 26 single-letter strings!')

        self.s = list(s)
        self.e = e if e else self.__error()

    def jump(self):
        n = len(self.s) - 1
        while True:
            a, b = random.randint(0, n), random.randint(0, n)
            if a != b:
                self.s[a], self.s[b] = self.s[b], self.s[a]
                self.e = self.__error()
                return

    def __error(self):
        global Sentences
        return sum(-math.log(
                       State.sentence_likelihood(
                           WSEP.join(
                               ''.join(self.s[x]
                               for x in w)
                           for w in s) + WSEP)
                   )
               for s in Sentences)

    def __str__(self):
        global Sentences
        return '\n'.join(
                   ' '.join(
                       ''.join(self.s[x]
                       for x in w)
                   for w in s)
               for s in Sentences)

    def sentence_likelihood(s):
        global NGram
        prev = tuple(WSEP for _ in range(NGram['size'] - 1))
        p    = 1.
        for l in s:
            #p *= 2. * NZ * math.exp(-NZ / 1.05) if prev not in NGram else NGram[prev][l]
            p *= NZ if prev not in NGram else NGram[prev][l]
            if p == 0.:
                return sys.float_info.min
            prev = prev[1:] + (l,)
        return p

def main():
    global NGram, Sentences
    Sentences = parse_input()
    NGram     = build_ngram()
    mapping   = minimize   ()

    log   (mapping)
    render(mapping)

def parse_input():
    sentences = []
    w         = []
    for s in sys.stdin.readlines():
        l = tuple(map(int, s.strip().split()))
        if l[0] == -1:
            sentences.append(tuple(w))
            w = []
            continue
        w.append(l)
    if len(w) > 0:
        sentences.append(tuple(w))
    return tuple(sentences)

def log(*args, **kwargs):
    if 'file' in kwargs:
        del kwargs['file']
    print(*args, file = sys.stderr, **kwargs)
    sys.stderr.flush()

def build_ngram(n = NGRAM_SIZE):
    if os.path.exists(NGRAM_CACHE):
        with open(NGRAM_CACHE, 'rb') as f:
            ngram = pickle.load(f)
            if 'size' in ngram and ngram['size'] == n:
                return ngram

    log('Constructing {}-gram from training data (this may take a while)...'.format(n), end = '')
    ngram         = {}
    ngram['size'] = n

    defp = {}
    for l in string.ascii_lowercase:
        defp[l] = 1
    defp[WSEP] = 1

    with bz2.open(CORPUS_FILE, 'rt') as f:
        for s in f.readlines():
            prev = tuple(WSEP for _ in range(n - 1))
            for w in tuple(re.sub(r'[^a-z]', r'', t.lower()) + WSEP for t in s.strip().split()):
                for l in w:
                    if prev not in ngram:
                        ngram[prev] = dict(defp)
                    ngram[prev][l] += 1
                    prev = prev[1:] + (l,)

    for prev in ngram.keys():
        if prev == 'size':
            continue
        following = ngram[prev]
        total = sum(following.values())
        for lk in following.keys():
            following[lk] /= total
            #following[lk] *= 2. * math.exp(-following[lk] / 1.05)

    with open(NGRAM_CACHE, 'wb') as f:
        pickle.dump(ngram, f, pickle.HIGHEST_PROTOCOL)
    log('done!')
    return ngram

def minimize():
    random.seed(SEED)
    random.shuffle(ALPHABET) # Shake to make it more interesting.
    old, best = State(), None
    log('Decoding...')
    sys.stderr.write('\033[2J')
    for k in range(ITERATIONS):
        t = T(k / ITERATIONS)
        sys.stderr.write('\033[H')
        for i in range(ADJUST):
            new = State(old.s)
            new.jump()
            if new.e < old.e or random.random() < math.exp(-(new.e - old.e) / (K * t)):
                log('Current (temp: {:4.2f} err: {:4.2f} delta: {:4.2f}):'.format(t, new.e, abs(old.e - new.e)), end = '\r')
                old = State(new.s, new.e)
                if not best or new.e < best.e:
                    best = State(new.s, new.e)
        log('\n{}\n\nBest (err: {:4.2f}):\n{}'.format(new, best.e, best))
    log('\ndone!')
    return best

def render(mapping):
    # Dotted numbers are dimensions represented in millimeters.
    l = Layout(fontname   = 'Sans'   ,
               fontsize   = 32       ,
               pagewidth  = 210. / MM,
               pageheight = 297. / MM,
               margins    = 50.  / MM,
               colwidth   = 70.  / MM,
               rowheight  = 15.  / MM,
               xtextsep   = 25.  / MM,
               ytextsep   = 6.75 / MM,
               tilesize   = 10.  / MM,
               rows       = 12       )

    pdf = cairo.PDFSurface(PDFOUT, l.pagewidth, l.pageheight)
    cr  = cairo.Context(pdf)

    cr.select_font_face(l.fontname)
    cr.set_font_size   (l.fontsize)

    for i in range(24):
        x = l.margins + l.colwidth  * (i // l.rows)
        y = l.margins + l.rowheight * (i %  l.rows)
        tile = cairo.ImageSurface.create_from_png(os.path.join(DATAP, '{}.png'.format(i)))
        ext = cr.text_extents(mapping.s[i])
        cr.move_to(x + l.xtextsep - (ext[2] / 2. + ext[0]),
                   y + l.ytextsep - (ext[3] / 2. + ext[1]))
        cr.show_text(mapping.s[i])
        cr.save()
        s = min(l.tilesize / tile.get_width (),
                l.tilesize / tile.get_height())
        cr.translate(x, y)
        cr.scale(s, s)
        cr.set_source_surface(tile, 0, 0)
        cr.paint()
        cr.restore()
        tile.finish()
    pdf.finish()

if __name__ == '__main__':
    main()
