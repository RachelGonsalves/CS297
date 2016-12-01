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
import re
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
def bits_raw(f):
    while True:
        chByte = f.read(1)
        if not chByte:
            break
        numByte = ord(chByte)
        print("num: %d, bin: %s" % (numByte, "{0:08b}".format(numByte)) )
        for i in xrange(8):
            yield (numByte >> i) & 1

def bits(f):
    bytesFound = 0
    while True:
        chByte = f.read(1)
        if not chByte:
            break
        bytesFound += 1
        numByte = ord(chByte)
        # guaranteed to have byte boundary due to AES
        bitsStr = "{0:08b}".format(numByte)
        bitsStrLE = bitsStr[::-1] # string.reverse: handling little-endianness
        for b in bitsStrLE:
            yield int(b)
    print("encoding.bytesFound: %d" % bytesFound)

def binary2Long(f, n):
    v1 = long(1)
    idx = 0
    val = 0
    bitsCount = 0
    for b in bits(f):
        bitsCount += 1
        if idx == n:
            yield val
            idx = 0
            val = v1 & b
        else:
            if b == 1:
                v = v1 << idx
                val += v
        idx += 1
    print("encoding.bitsFound : %d, n : %d" % (bitsCount, n))
    if val > 0:
        print("Adding %d pad" % (n - idx))
        while idx != n: # append 0s to match n boundary- needed to ignore the offset while decoding
            val << 1
            idx += 1
        yield val

#pat = '/home/rachel1105g/nltk_data/corpora/brown/'
pat = 'test_data/'
pat = 'small_data/'

def main_encode(wordList, tagIndices, n):

    # assuming all state lists end with 'period'
    STATES1 = ['JJ', 'NN', 'VB', 'period'] #adjective noun verb period
    STATES2 = ['NN', 'VB', 'RB', 'period']# noun verb adverb period
    STATES3 = ['NN', 'VB', 'IN', 'NN','period']# noun verb preposition noun period
    stateIndex = 0
    STATE_LIST =[STATES1,STATES2,STATES3]
    num = randint(0, 2)
    STATES = STATE_LIST[num]
    state = STATES[stateIndex]

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
            with open(os.path.abspath(filepath), "rb") as f_encrypted:
                longCount = 0
                for longval in binary2Long(f_encrypted, n):
                    #pull word form state and longval
                    longCount += 1
                    if state in tagIndices:
                        posIndex = tagIndices[state]
                        wrdIdx = posIndex[longval]
                        wrd = wordList[wrdIdx]
                        print("wrd: %s" % wrd)
                        wrdIdxStr += "%s, " % str(longval)
                        textStr += wrd
                        textStr += SPACE
                    else:
                        print("ERROR: state not found in tagIndices: %s" % state)

                    # perform state management
                    stateIndex += 1
                    state = STATES[stateIndex]
                    # if stateIndex == len(STATES):
                        # stateIndex = 0
                        # num = randint(0, 2)
                        # STATES = STATE_LIST[num]
                    if state == 'period': # assuming all state lists end with 'period'
                        textStr = textStr[:-1] # remove trailing space
                        textStr += '.'
                        textStr += SPACE
                        stateIndex = 0
                        num = randint(0, 2)
                        STATES = STATE_LIST[num]
                        state = STATES[stateIndex]

                    print("longCount: %d | wordCount: %d" % (longCount, len(re.findall(r'\w+', textStr))))
                print("encoding.longCount: %d" % longCount)

            encoded_file = str(filepath) + ".enc"
            with io.FileIO(encoded_file, "w") as file:
                file.write(textStr)
                textStr = ""

            encoded_idx_file = str(filepath) + ".wrdlstidx.enc"
            with io.FileIO(encoded_idx_file, "w") as file:
                file.write(wrdIdxStr)
                wrdIdxStr = ""

    print("encoding over")

'''
    DECODING:
'''
def read_bit_str(f, wordList, tagIndices, n, debugStreamer = None):
    wrdCount = 0
    for line in f:
        for word in line.split():
            wrdCount += 1
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
                            debugStreamer('LONG', val)
                        found = True
                        break
                if not found:
                    print("ERROR: Encoded Word not found in any taglist: %s" % wrd)
                # for each taggedIndex, find id where index[longval] = id
                # meaning: longval = tagindex.index(id)
                formatStr = "{0:0%db}" % n
                textBinary = formatStr.format(val) # N chars : binary N bits of encrypted data
                # print(textBinary)
                # if debugStreamer:
                #     debugStreamer('BIN', textBinary)
                textBinaryLE = textBinary[::-1] # string.reverse: handling little-endianness
                for c in textBinaryLE: #n bits
                    yield c
            else:
                print("ERROR: Encoded Word not found wrdList: %s" % wrd)
    print("Decoding.wrdCount: %d" % wrdCount)

def read_octet_str(f, wordList, tagIndices, n, debugStreamer = None):
    binTxt = ""
    idx = 0
    for c in read_bit_str(f, wordList, tagIndices, n, debugStreamer):
        binTxt += c
        idx += 1
        if idx == 8:
            binTxtLE = binTxt[::-1] # string.reverse: handling little-endianness
            yield binTxtLE # 8 bits out of n bits
            idx = 0
            binTxt = ""
    # if binTxt: # ignore last unaligned bits
    #     yield binTxt

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
