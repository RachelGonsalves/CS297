import math, pickle, struct, io, binascii,re, os,random, hashlib
import numpy as np
from Crypto.Cipher import AES
from practice import TOE_HMM_CHARS
model = TOE_HMM_CHARS.loadHMM('brown_chars_N6.hmm')

lis = [1/math.pow(2,i) for i in range(20)]

#Rounding
def rounding(A):
    for row in A:
        for id_i, val_i in enumerate(row):
            for id_j, val_j in enumerate(lis):
                if val_i > val_j:
                    mean = (lis[id_j-1] + val_j)/2
                    if val_i >= mean:
                        row[id_i] = (lis[id_j - 1])
                        break
                    else:
                        row[id_i] = val_j
                        break

    for id,row in enumerate(A):
        if sum(row) != 1:
            diff = 1 - sum(row)
            row_min = min(row)
            if row_min == 0:
                temp_row = [x for x in row if x != 0]
                minimum = min(temp_row)
                row_reversed = row[::-1]
                id = row_reversed.index(minimum)
                row_reversed[id] += diff
                row_new = row_reversed[::-1]
                for i,v in enumerate(row):
                    row[i] = row_new[i]
    return A

def div(a,b):
    if b == 0:
        return 1
    else:
        return (a/b)

#Binarization
def binarization(A):
    # taking already rounded probabilities
    # sorting each row transition matrix A in descending order and storing in ORP and storing index in IRP
    ORP, IRP, BIN_ORP,BIN_RP= ([] for i in range(4))

    for row in A:
        descSortedRow = sorted(enumerate(row), key=lambda x: x[1], reverse=True)
        IRP.append([i[0] for i in descSortedRow]) # Key is the value, Lambda function chooses the value from each tuple for sorting
        ORP.append([i[1] for i in descSortedRow]) #http://stackoverflow.com/questions/6422700/how-to-get-indices-of-a-sorted-array-in-python/6423325#6423325
    print(IRP)
    print(ORP)

    for row_ORP in ORP:
        row_BIN_ORP = []
        row_BIN_ORP.append(0)

        last_input = row_ORP[0]
        last_output = row_BIN_ORP[0]
        num = int(math.log(int(div(1,row_ORP[0])),2))
        k = len(row_ORP)

        j = 1
        while j<k:
            if row_ORP[j] == 0:
                row_BIN_ORP.append('-')
            elif row_ORP[j] == last_input:
                row_BIN_ORP.append(int(last_output + 1))
                diff = int(math.log(int(div(1,row_ORP[j])), 2)) - num
            else:
                diff = int(math.log(int(div(1,row_ORP[j])),2)) - num
                row_BIN_ORP.append(int((last_output + 1) * (math.pow(2,diff))))
                num = int(math.log(int(div(1,row_ORP[j])),2))

            last_input = row_ORP[j]
            last_output = (last_output + 1) * (math.pow(2,diff))
            j += 1

        BIN_ORP.append(row_BIN_ORP)


    for row in IRP:
        tup = zip(row,BIN_ORP[IRP.index(row)])
        BIN_RP.append([bin(i[1]) if i[1] is not '-' else '-' for i in sorted(tup, key=lambda x: x[0])])

    return BIN_RP

l = str(27)

with open('outA'+l+'.txt', 'rb') as fp:
    tran_mat = pickle.load(fp)
    tran_mat = rounding(tran_mat)
    print('{}{}'.format("Transition matrix A: ", tran_mat))
    binary_tran_mat =  binarization(tran_mat)
    print('{}'.format("Binary Transition matrix A: "))
    for row in binary_tran_mat:
        print(row)


with open('outB'+l+'.txt', 'rb') as fp:
    B = pickle.load(fp)
    B_argmax = [max(row) for row in B]
    B_letter = [np.where(row == max(row)) for row in B]
    letter = []
    print(B_letter)
    print(B_argmax)
    for i in B_letter:
        if i[0][0] == 26:
            letter.append(' ')
        else:
            letter.append(chr(i[0][0]+97))
    descSortedB = []
    for row in B:
        descSortedB_row = sorted(enumerate(row), key=lambda x: x[1], reverse=True)
        descSortedB.append(descSortedB_row)
    print(descSortedB)


with open('outPI'+l+'.txt', 'rb') as fp:
    pi = pickle.load(fp)
    pi_argmax = max(pi)
    print(pi)
    ord_pi = [x[0] for x in sorted(enumerate(pi), key=lambda x: x[1], reverse=True)]
    print('{}{}'.format("ord PI: ", ord_pi))


def bits(f):
    bytesFound = 0
    stream = []
    while True:
        chByte = f.read(1)
        if not chByte:
            break
        bytesFound += 1
        numByte = ord(chByte)
        # guaranteed to have byte boundary due to AES
        bitsStr = "{0:08b}".format(numByte)
        bitsStrLE = bitsStr[::-1]  # string.reverse: handling little-endianness
        stream.append(bitsStrLE)
    return stream

descB = descSortedB

#Emission graph
N = len(binary_tran_mat)
emission_graph = [['-']*N for i in range(N)]

def elem(num):
    if num == 26:
        b = ' '
    else:
        b = chr(num + 97)
    return b

for i in range(N):
    for j in range(N):
        flag = True
        if len(descB[j]) != 0:
            let = elem((descB[j][0])[0])
            if let in emission_graph[i]:
                while flag:
                    for k in range(1,len(descB[j])):
                        if elem((descB[j][k])[0]) not in emission_graph[i]:
                            flag = False
                            let = elem(((descB[j]).pop(k))[0])
                            break
                    m = 0
                    while flag:
                        for l in range(len(descB[m])):
                            if elem((descB[m][l])[0]) not in emission_graph[i]:
                                flag = False
                                let = elem(((descB[m]).pop(l))[0])
                                break
                        m +=  1
            else:
                let = elem((descB[j].pop(0))[0])
        else:
            m = 0
            while flag:
                if len(descB[m]) != 0:
                    for l in range(len(descB[m])):
                        if elem((descB[m][l])[0]) not in emission_graph[i]:
                            flag = False
                            let = elem(((descB[m]).pop(l))[0])
                            break
                m += 1
        emission_graph[i][j] = let


# print('{}{}'.format("Emission Graph: ", emission_graph))

#ENCODING

start_state, = np.where(pi == pi_argmax)
initial_start_state = int(start_state[0])


pat = 'letter/27/'
for fil in os.listdir(pat):
    start_state = initial_start_state
    if (fil.endswith('.encr')) and os.path.exists(pat + fil):
        filepath = os.path.join(pat, fil)
        print(filepath)
        with open(os.path.abspath(filepath), "rb") as f:
            encoded_stream = ""

            stream = bits(f)
            newstream = "".join(stream)

            prev = 0
            replacement = 0
            current_stream_start = 0
            while current_stream_start != len(newstream):
                if newstream[current_stream_start:].startswith('0'):
                    replacement = '0'
                else:
                    for i in binary_tran_mat[start_state]:
                        if newstream[current_stream_start:].startswith(i[2:]):
                            if len(i[2:]) > prev:
                                replacement = i[2:]
                            prev = len(i[2:])

                next_state = binary_tran_mat[start_state].index('0b' + replacement)
                encoded_stream += emission_graph[start_state][next_state]
                start_state = next_state
                current_stream_start += len(replacement)
        encoded_file = str(filepath) + ".enc"
        with io.FileIO(encoded_file, "w") as file:
            file.write(encoded_stream)
#DECODING
    rev_start_state = initial_start_state
    if (fil.endswith('.enc')) and os.path.exists(pat + fil):
        filepath = os.path.join(pat, fil)
        print(filepath)
        with open(os.path.abspath(filepath), "rb") as f:
            decoded_stream = ""
            for i in encoded_stream:
                rev_next_state = emission_graph[rev_start_state].index(i)
                decoded_stream += binary_tran_mat[rev_start_state][rev_next_state][2:]
                rev_start_state = rev_next_state
            print(decoded_stream == newstream)

            # strt = 0
            # actual_string = ""
            # write_stream = ""
            # write_stream += (int(decoded_stream, 2)).decode('utf-8')
            # while (strt+8) != len(decoded_stream):
            #     strm = decoded_stream[strt:strt + 8]
            #     strm = (strm.lstrip("0"))
            #     strt += 8
            #     write_stream = chr(strm)
                # write_stream += (struct.pack('B', int(strm)))
                # write_stream += ('%x' % int(strm, 2)).decode('hex').decode('utf-8')

                # write_stream =(''.join([chr(int(x, 2)) for x in re.split('(........)',actual_string) if x])).decode('utf-8')
            # decoded_file = str(filepath) + ".dec"
            # with io.FileIO(decoded_file, "w") as file:
            #     file.write(write_stream)


# if decoded_stream == newstream:
#     print("decoded_stream MATCHES to new stream")
# else:
#     print("decoded_stream DOES NOT MATCH to new stream")