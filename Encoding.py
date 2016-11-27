import math
import os
import io
import random
from random import randint
import nltk
from nltk.corpus import brown
from collections import defaultdict

wordList = []
tagIndices = {}
WHITE_LIST = ['NN','JJ','IN','RB','VB']


def update(tagIndex, tag, wordIndex):
    if tag not in tagIndex:
        tagWords = []
        tagIndex[tag] = tagWords
    else:
        tagWords = tagIndex[tag]
    tagWords.append(wordIndex)


def createDict():
    global wordList
    global tagIndices
    global WHITE_LIST
    taggedWords = brown.tagged_words()    #http://www.scs.leeds.ac.uk/amalgam/tagsets/brown.html
    for id, tuple in enumerate(taggedWords):
        word = tuple[0]
        tag = tuple[1]
        if tag in WHITE_LIST:
            wordList.append(word)
            update(tagIndices, tag, len(wordList) - 1)


def bits(f):
    bytes = (ord(b) for b in f.read())
    for b in bytes:
        for i in xrange(8):
            yield (b >> i) & 1

def binary2Long(f, n):
    v1 = long(1)
    idx = 0
    val = 0
    for b in bits(f):
        if idx == n:
            yield val
            v = v1 & b
            idx = 1
            val = v
        else:
            if b == 1:
                v = v1 << idx
                val += v
            idx += 1
    if val > 0:
        yield val

createDict()

dict_size = min([len(v) for k,v in tagIndices.items()])

n = int(math.floor(math.log(dict_size, 2))) # n is the number of bits to be replaced/block size
print(n)

pat = '/home/rachel1105g/nltk_data/corpora/brown/'


STATES1 = ['JJ', 'NN', 'VB', 'period'] #adjective noun verb period
STATES2 = ['NN', 'VB', 'RB', 'period']# noun verb adverb period
STATES3 = ['NN', 'VB', 'IN', 'NN','period']# noun verb preposition noun period
stateIndex = 0
STATE =[STATES1,STATES2,STATES3]
num = randint(0, 2)
STATES = STATE[num]

SPACE = " "
textStr = ""
fileCount =  4
for fil in os.listdir(pat):
    if (fil.endswith(".enc")) and os.path.exists(pat + fil):
        filepath = os.path.join(pat, fil)
        print filepath
        fileCount -= 1
        if fileCount == 2:
            break
        f = open(os.path.abspath(filepath), "rb")
        for longval in binary2Long(f, n):
            if stateIndex == len(STATES):
                stateIndex = 0
                num = randint(0, 2)
                STATES = STATE[num]

            state = STATES[stateIndex]
            if state in tagIndices:
                index = tagIndices[state]

                # tagLen = len(index)
                idx = longval
                wrdIdx = index[idx]
                wrd = wordList[wrdIdx]
                textStr += wrd
                textStr += SPACE
            else:
                textStr = textStr[:-1]
                textStr += '.'
                textStr += SPACE
            stateIndex += 1

        encoded_file = str(filepath) + ".txt"
        with io.FileIO(encoded_file, "w") as file:
            file.write(textStr)
            textStr = ""

print(textStr)
f.close()
print("encoding over")

textSt = ""
for fil in os.listdir(pat):
    if (fil.endswith(".enc.txt")) and os.path.exists(pat + fil):
        filepath = os.path.join(pat, fil)
        print filepath
        f = open(os.path.abspath(filepath), "rb")
        for line in f:
            for word in line.split():
                wrd = word.replace(".","")
                if wrd in wordList:
                    id = wordList.index(wrd)
                    # id = id%n
                    text = '{0:015b}'.format(id)
                    textSt += text

        decoded_file = str(filepath) + ".dec"
        with io.FileIO(decoded_file, "wb") as file:
                file.write(textSt)
                textSt = ""
f.close()


