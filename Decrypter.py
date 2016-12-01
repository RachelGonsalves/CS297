import os, random, struct
import hashlib
from Crypto.Cipher import AES

password = 'Rachel'
keyin = hashlib.sha256(password).digest()

# pat = '/home/rachel1105g/nltk_data/corpora/brown/'
pat = 'test_data/'

pat = 'small_data/'


def decrypt_file(key, in_filename, out_filename=None, chunksize=24*1024):
    """ Decrypts a file using AES (CBC mode) with the
        given key. Parameters are similar to encrypt_file,
        with one difference: out_filename, if not supplied
        will be in_filename without its last extension
        (i.e. if in_filename is 'aaa.zip.enc' then
        out_filename will be 'aaa.zip')
    """
    if not out_filename:
        out_filename = in_filename + '.decr'

    with open(in_filename, 'rb') as infile:
        origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
        iv = infile.read(16)
        decryptor = AES.new(key, AES.MODE_CBC, iv)

        with open(out_filename, 'wb') as outfile:
            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    print("Empty chunk")
                    break
                else:
                    # print(chunk)
                    outfile.write(decryptor.decrypt(chunk))

            outfile.truncate(origsize)

for fil in os.listdir(pat):
    if (fil.endswith('enc.dec')) and os.path.exists(pat + fil):
        print(fil)
        decrypt_file(keyin, pat+fil)