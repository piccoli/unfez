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
NAL         = '|'
SEED        = 130000
ADJUST      = 256
K           = 20.
ITERATIONS  = 512
T           = lambda x: .9975 ** (x * 1e3)
NZ          = 1e-1
DATAP       = os.path.join('data', 'avg')
PDFOUT      = 'fezetta.pdf'
MM          = 25.4 * .013837 # Base unit is points.

Layout = namedtuple('Layout', 'margins colwidth rowheight rows xtextsep ytextsep pagewidth pageheight fontsize fontname tilesize')

class State:
    def __init__(self, s = list(string.ascii_lowercase), e = None):

        if type(s) != list:
            raise TypeError("'list' expected, but received a '{}' instead!".format(type(s)))

        if len(s) != 26 or not all(map(lambda x: type(x) is str and len(x) == 1, s)):
            raise ValueError('You must provide a list containing exactly 26 single-letter strings!')

        self.s = list(s)
        #random.shuffle(self.s)
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
        return sum(-math.log(
                       State.sentence_likelihood(
                           NAL.join(
                               ''.join(self.s[x]
                               for x in w)
                           for w in s) + NAL)
                   )
               for s in Sentences)

    def __str__(self):
        return '\n'.join(
                   ' '.join(
                       ''.join(self.s[x]
                       for x in w)
                   for w in s)
               for s in Sentences)

    def sentence_likelihood(s):
        prev = tuple(NAL for _ in range(NGram['size'] - 1))
        p    = 1.
        for l in s:
            #p *= 2. * NZ * math.exp(-NZ / 1.05) if prev not in NGram else NGram[prev][l]
            p *= NZ if prev not in NGram else NGram[prev][l]
            if p == 0.:
                return sys.float_info.min
            prev = prev[1:] + (l,)
        return p

def main():
    random.seed(SEED)
    parse_input()
    build_ngram(NGRAM_SIZE)
    mapping = minimize()
    log(mapping)
    render(mapping)

def parse_input():
    global Sentences
    Sentences = []
    w         = []
    for s in sys.stdin.readlines():
        l = list(map(int, s.strip().split()))
        if l[0] == -1:
            Sentences.append(w)
            w = []
            continue
        w.append(l)
    if len(w) > 0:
        Sentences.append(w)

def log(*args, **kwargs):
    if 'file' in kwargs:
        del kwargs['file']
    print(*args, file = sys.stderr, **kwargs)
    sys.stderr.flush()

def build_ngram(n = 4):
    global NGram

    if os.path.exists(NGRAM_CACHE):
        with open(NGRAM_CACHE, 'rb') as f:
            NGram = pickle.load(f)
            if 'size' in NGram and NGram['size'] == n:
                return

    log('Constructing {}-gram from training data (this may take a while)...'.format(NGRAM_SIZE), end = '')
    NGram         = {}
    NGram['size'] = n

    defp = {}
    for l in string.ascii_lowercase:
        defp[l] = 1
    defp[NAL] = 1

    with bz2.open(CORPUS_FILE, 'rt') as f:
        for s in f.readlines():
            prev = tuple(NAL for _ in range(n - 1))
            for w in tuple(re.sub(r'[^a-z]', r'', t) + NAL for t in s.strip().split()):
                for l in w:
                    if prev not in NGram:
                        NGram[prev] = dict(defp)
                    NGram[prev][l] += 1
                    prev = prev[1:] + (l,)

    for prev in NGram.keys():
        if prev == 'size':
            continue
        following = NGram[prev]
        total = sum(following.values())
        for lk in following.keys():
            following[lk] /= total
            #following[lk] *= 2. * math.exp(-following[lk] / 1.05)

    with open(NGRAM_CACHE, 'wb') as f:
        pickle.dump(NGram, f, pickle.HIGHEST_PROTOCOL)
    log('done!')

def minimize():
    log('Decoding...')
    old, best = State(), None
    sys.stderr.write('\033[2J')
    for k in range(ITERATIONS):
        t = T(k / ITERATIONS)
        sys.stderr.write('\033[H')
        for i in range(ADJUST):
            new = State(old.s)
            new.jump()
            if new.e < old.e or random.random() < math.exp(-(new.e - old.e) / (K * t)):
                log('(temp: {:4.2f} err: {:4.2f} delta: {:4.2f})'.format(t, new.e, abs(old.e - new.e)), end = '\r')
                old = State(new.s, new.e)
                if not best or new.e < best.e:
                    best = State(new.s, new.e)
        log('\n{}\n\nbest (err: {:4.2f})\n{}'.format(new, best.e, best))
    log('\ndone!')
    return best

def render(mapping):
    # Dotted numbers are dimensions represented in millimeters.
    l = Layout(margins    = 50.   ,
               colwidth   = 70.   ,
               rowheight  = 15.   ,
               rows       = 13    ,
               xtextsep   = 25.   ,
               ytextsep   = 6.5   ,
               pagewidth  = 210.  ,
               pageheight = 297.  ,
               fontsize   = 32    ,
               fontname   = 'Sans',
               tilesize   = 10.   )

    pdf = cairo.PDFSurface(PDFOUT, l.pagewidth / MM, l.pageheight / MM)
    cr  = cairo.Context(pdf)

    cr.select_font_face(l.fontname)
    cr.set_font_size   (l.fontsize)

    for i in range(26):
        x = (l.margins + l.colwidth  * (i // l.rows)) / MM
        y = (l.margins + l.rowheight * (i %  l.rows)) / MM
        tile = cairo.ImageSurface.create_from_png(os.path.join(DATAP, '{}.png'.format(i)))
        ext = cr.text_extents(mapping.s[i])
        cr.move_to(x + l.xtextsep / MM - (ext[2] / 2. + ext[0]),
                   y + l.ytextsep / MM - (ext[3] / 2. + ext[1]))
        cr.show_text(mapping.s[i])
        cr.save()
        s = min(l.tilesize / MM / tile.get_width (),
                l.tilesize / MM / tile.get_height())
        cr.translate(x, y)
        cr.scale(s, s)
        cr.set_source_surface(tile, 0, 0)
        cr.paint()
        cr.restore()
        tile.finish()
    pdf.finish()

if __name__ == '__main__':
    main()
