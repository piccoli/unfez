unFEZ
========

A *very* crude (but equally fun) experiment for performing
automated cryptanalysis on FEZ's ((C) Polytron Corporation)
encoded alphabet.

Just take any in-game screen shot featuring an encoded balloon
dialog (only works on 1920x1080 images for now), and type the
following on your (UNIX shell or alike) command line:

./shot2text.py screenshot.png | ./unfez.py

or, for a demo, just try one of the already available input files:

./unfez.py < all.in

The decoded message should automagically appear on the output,
along with a PDF depicting the translated alphabet
(fezetta.pdf).

FEZ uses a simple substitution cipher
(http://en.wikipedia.org/wiki/Substitution_cipher) to encode its
hidden messages, and in fact it is quite easy (albeit tedious) to
figure out the encoding by hand.  However, automating this task is
not as trivial, so it is an interesting programming challenge.
Plus, with a few changes, this code should work with *any*
substitution alphabets!

The decoding algorithm first constructs a 4-gram
(http://en.wikipedia.org/wiki/Ngram) table from an English language
training set. Next, an MCMC method is applied to find the alphabet
permutation that produces the sentence with maximum likelihood.

There is a lot of room for improvement in the code
performance-wise, especially in shot2text.py, where a
semi-brute-force template matching method is used for extracting
the symbols from a screen shot.

In addition, success in decoding a message may vary, depending on
the size of the input sentence. It works best with medium-sized
sentences, such as the example in 4.in, or using multiple
sentences, such as in all.in.  Furthermore, as FEZ's alphabet uses
the same symbol for both 'u' and 'v' and I couldn't find the
remaining two symbols (if they exist, that is), your decoded
message may look imperfect at times. :)

Please also note that this program is intended simply as an
experimental tool and is far from being a solid or bug-free piece
of software. Try it at your own risk! (Should be pretty harmless
though.) I've only tested on a Linux machine, but it should work
on modern UNIXes with Python3 + Pillow + Pycairo libraries.
