import math
import os
import io
import random
from random import randint
import nltk
from nltk.corpus import brown
from collections import defaultdict
import pickle
import struct
# import binascii

WHITE_LIST = ['NN','JJ','IN','RB','VB']


def update(tagIndex, tag, wordIndex):
    if tag not in tagIndex:
        tagWords = []
        tagIndex[tag] = tagWords
    else:
        tagWords = tagIndex[tag]
    tagWords.append(wordIndex)


def createDict():
    global WHITE_LIST
    wordList = []
    tagIndices = {}
    taggedWords = brown.tagged_words()    #http://www.scs.leeds.ac.uk/amalgam/tagsets/brown.html
    for id, tuple in enumerate(taggedWords):
        word = tuple[0]
        tag = tuple[1]
        if tag in WHITE_LIST:
            if word not in wordList:
                wordList.append(word)
                update(tagIndices, tag, len(wordList) - 1)
    return (wordList, tagIndices)

def saveDict(filename, wordList, tagIndices, n):
    import pickle
    model = {'wordList': wordList, 'tagIndices': tagIndices, 'n': n}
    s = pickle.dumps(model)
    with open(filename, 'w') as f:
        f.write(s)

def loadDict(filename):
    with open(filename, 'r') as f:
        modelSerialized = f.read()
    model = pickle.loads(modelSerialized)
    
    wordList = model['wordList']
    tagIndices = model['tagIndices']
    n = model['n']
    return (wordList, tagIndices, n)

'''
ENCODING:
'''
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

#pat = '/home/rachel1105g/nltk_data/corpora/brown/'
pat = 'test_data/'
pat = 'small_data/'

def main_encode(wordList, tagIndices, n):

    STATES1 = ['JJ', 'NN', 'VB', 'period'] #adjective noun verb period
    STATES2 = ['NN', 'VB', 'RB', 'period']# noun verb adverb period
    STATES3 = ['NN', 'VB', 'IN', 'NN','period']# noun verb preposition noun period
    stateIndex = 0
    STATE =[STATES1,STATES2,STATES3]
    num = randint(0, 2)
    STATES = STATE[num]

    SPACE = " "
    textStr = ""
    wrdIdxStr = ""
    fileCount =  4
    for fil in os.listdir(pat):
        if (fil.endswith('.encr')) and os.path.exists(pat + fil):
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
                    posindex = tagIndices[state]

                    # tagLen = len(index)
                    idx = longval
                    wrdIdx = posindex[idx]
                    wrd = wordList[wrdIdx]
                    wrdIdxStr += "%s, " % str(wrdIdx)
                    textStr += wrd
                    textStr += SPACE
                else:
                    textStr = textStr[:-1]
                    textStr += '.'
                    textStr += SPACE
                stateIndex += 1

            encoded_file = str(filepath) + ".enc"
            encoded_idx_file = str(filepath) + ".wrdlstidx.enc"
            with io.FileIO(encoded_file, "w") as file:
                file.write(textStr)
                textStr = ""
            with io.FileIO(encoded_idx_file, "w") as file:
                file.write(wrdIdxStr)
                wrdIdxStr = ""

    print(textStr)
    f.close()
    print("encoding over")

'''
    DECODING:
'''
def read_bit_str(f, wordList, tagIndices, n, debugStreamer = None):
    for line in f:
        for word in line.split():
            wrd = word.replace(".","")
            if wrd in wordList:
                id = wordList.index(wrd) # position of word in posindex
                # print("FOUND: %s : %d" % (wrd, id))
                found = False
                for posIndex_i in WHITE_LIST:
                    if id in tagIndices[posIndex_i]:
                        # print(id)
                        val = tagIndices[posIndex_i].index(id) # can optimize search by finding word tag
                        # val is the long value corresponding to N bits of encrypted data
                        # print(val)
                        if debugStreamer: 
                            debugStreamer('LONG', id)
                        found = True
                        break
                if not found:
                    print("ERROR: Encoded Word not found in any taglist: %s" % wrd)
                # for each taggedIndex, find id where index[longval] = id
                # meaning: longval = tagindex.index(id)
                formatStr = "{0:0%db}" % n
                textBinary = formatStr.format(val) # N chars : binary N bits of encrypted data
                # print(textBinary)
                if debugStreamer:
                    debugStreamer('BIN', textBinary)
                for c in textBinary: #n bits
                    yield c
            else:
                print("ERROR: Encoded Word not found wrdList: %s" % wrd)

def read_octet_str(f, wordList, tagIndices, n, debugStreamer = None):
    binTxt = ""
    idx = 0
    for c in read_bit_str(f, wordList, tagIndices, n, debugStreamer):
        binTxt += c
        idx += 1
        if idx == 8:
            yield binTxt # 8 bits out of n bits
            idx = 0
            binTxt = ""
    if binTxt:
        yield binTxt

def debugStreamerProvider(decoded_idx_file):
    flong = open(decoded_idx_file, 'w')
    fbin = open(decoded_idx_file + '.bin', 'w')

    def debugStreamerFn(type, data):
        if type == 'BIN':
            fbin.write("%s, " % str(data))
        elif type == 'LONG':
            flong.write("%s, " % str(data))

    def cleaner():
        fbin.close()
        flong.close()

    return (debugStreamerFn, cleaner)

def main_decode(wordList, tagIndices, n):
    for fil in os.listdir(pat):
        if (fil.endswith('.encr.enc')) and os.path.exists(pat + fil):
            filepath = os.path.join(pat, fil)
            print filepath
            with open(os.path.abspath(filepath), "ro") as inFile: # input file
                decoded_file = str(filepath) + ".dec"
                decoded_idx_file = str(filepath) + ".wrdlstidx.dec"
                print(decoded_file)

                (debugStreamer, cleaner) = debugStreamerProvider(decoded_idx_file)
                with open(decoded_file, "wb") as outFile: # output file
                    # read 8 bits from input file as chars
                    for octet in read_octet_str(inFile, wordList, tagIndices, n, debugStreamer):
                        if len(octet) != 8:
                            octet = '0' * (8 - len(octet)) + octet
                        byteChar = struct.pack('B', int(octet, 2))
                        # byteBase64 = binascii.a2b_uu(octet) # !!!!!!!!! suspicious to be broken
                        outFile.write(byteChar)
                cleaner()

def main():
    # (wordList, tagIndices) = createDict()
    # dict_size = min([len(v) for k,v in tagIndices.items()])
    # n = int(math.floor(math.log(dict_size, 2))) # n is the number of bits to be replaced/block size
    # saveDict('brownTagModel', wordList, tagIndices, n)
    (wordList, tagIndices, n) = loadDict('brownTagModel')
    print(n)

    main_encode(wordList, tagIndices, n)
    main_decode(wordList, tagIndices, n)

if __name__ == "__main__":
    main()
