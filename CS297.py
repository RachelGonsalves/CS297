import os, random, struct
import hashlib
from Crypto.Cipher import AES


# http://eli.thegreenplace.net/2010/06/25/aes-encryption-of-files-in-python-with-pycrypto

def encrypt_file(key, in_filename, out_filename=None, chunksize=64 * 1024):
    # type: (object, object, object, object) -> object
    """ Encrypts a file using AES (CBC mode) with the
        given key.

        key:
            The encryption key - a string that must be
            either 16, 24 or 32 bytes long. Longer keys
            are more secure.

        in_filename:
            Name of the input file

        out_filename:
            If None, '<in_filename>.enc' will be used.

        chunksize:
            Sets the size of the chunk which the function
            uses to read and encrypt the file. Larger chunk
            sizes can be faster for some files and machines.
            chunksize must be divisible by 16.
    """
    if not out_filename:
        out_filename = in_filename + '.encr'

    iv = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    filesize = os.path.getsize(in_filename)

    with open(in_filename, 'rb') as infile:
        with open(out_filename, 'wb') as outfile:
            outfile.write(struct.pack('<Q', filesize))
            outfile.write(iv)

            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    chunk += ' ' * (16 - len(chunk) % 16)

                outfile.write(encryptor.encrypt(chunk))


password = 'Rachel'
keyin = hashlib.sha256(password).digest()

pat = '/home/rachel1105g/nltk_data/corpora/brown/'
pat = 'test_data/'
pat = 'small_data/'

for fil in os.listdir(pat):
    print(fil)
    if (os.path.exists(pat+fil)):
        encrypt_file(keyin, pat+fil)


