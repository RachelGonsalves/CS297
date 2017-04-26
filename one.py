import math, pickle
import numpy as np

lis = [1/math.pow(2,i) for i in range(20)]
print(lis)

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
                # print(row_reversed[::-1])
                # print(A[id])
                row_new = row_reversed[::-1]
                for i,v in enumerate(row):
                    row[i] = row_new[i]

                # print(A[id])


    return A

def div(a,b):
    if b == 0:
        return 1
    else:
        return (a/b)

def binarization(A):
    # print(A)
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
        # row_BIN_ORP.append((int(math.log(int(div(1,row_ORP[0])),2))))
        row_BIN_ORP.append(0)

        last_input = row_ORP[0]
        last_output = row_BIN_ORP[0]
        num = int(math.log(int(div(1,row_ORP[0])),2))
        k = len(row_ORP)

        j = 1
        while j<k:
            if row_ORP[j] == 0:
                row_BIN_ORP.append('-')
                # diff = int(math.log(int(div(1, row_ORP[j])), 2)) - num
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
        # BIN_RP.append([bin(i[1]) for i in sorted(tup, key=lambda x: x[0])])
        BIN_RP.append([bin(i[1]) if i[1] is not '-' else '-' for i in sorted(tup, key=lambda x: x[0])])

    return BIN_RP
    # print(BIN_ORP)
    # print(BIN_RP)

with open('outA.txt', 'rb') as fp:
    tran_mat = pickle.load(fp)
    tran_mat = rounding(tran_mat)
    print('{}{}'.format("Transition matrix A: ", tran_mat))
    binary_tran_mat =  binarization(tran_mat)
    print('{}'.format("Binary Transition matrix A: "))
    for row in binary_tran_mat:
        print(row)


with open('outB.txt', 'rb') as fp:
    B = pickle.load(fp)
    B_argmax = [max(row) for row in B]
    B_letter = [np.where(row == max(row)) for row in B]
    letter = []
    print(B_letter)
    print(B_argmax)
    for i in B_letter:
        # print(i[0][0])
        if i[0][0] == 26:
            letter.append(' ')
        else:
            letter.append(chr(i[0][0]+97))
    print('{}{}'.format("Letter: ", letter))


with open('outPI.txt', 'rb') as fp:
    pi = pickle.load(fp)
    pi_argmax = max(pi)
    print(pi_argmax)


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
    # print("Stream: %s" % stream)


#ENCODING

start_state, = np.where(pi==pi_argmax)
# print(start_state[0])
initial_start_state = int(start_state[0])
start_state = int(start_state[0])
print(start_state)
print('{}{}'.format("start_state: ",start_state))
encoded_stream = ""
with open("testy_data/cb01.encr", 'rb') as f:
    stream = bits(f)
    # print("".join(stream))
    newstream = "".join(stream)
    print(newstream)

    print(binary_tran_mat[start_state - 1])

    prev = 0
    replacement = 0
    current_stream_start = 0
    while current_stream_start != len(newstream):
        # count = 0
        print(newstream[current_stream_start:])
        if newstream[current_stream_start:].startswith('0'):
            replacement = '0'
        else:
            for i in binary_tran_mat[start_state-1]:
                # print(i[2:])
                if newstream[current_stream_start:].startswith(i[2:]):
                    if len(i[2:]) > prev:
                        print("repli")
                        print(len(i[2:]))
                        replacement = i[2:]
                    prev = len(i[2:])

        encoded_stream = encoded_stream + letter[start_state]
        current_stream_start += len(replacement)
        next_state = binary_tran_mat[start_state - 1].index('0b' + replacement)
        start_state = next_state
        print(replacement)
        print(next_state)
        print(encoded_stream)

#DECODING

