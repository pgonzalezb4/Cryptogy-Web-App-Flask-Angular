from .cipher import Cipher, CryptAnalizer
import numpy as np
import copy
import random 
from typing import List
from PIL import Image
from Crypto.Cipher import DES
"""
Parameters        |  S-DES                       |  DES                         |
Plaintext Length  |  8 bits                      |  64 bits                     |
Ciphertext Length |  8 bits                      |  64 bits                     |
Key Length        |  10                          |  56                          |
Rounds operation  |  2                           |  16                          |
Number of subkeys |  2 keys (8 bits)             |  16 keys (54 bits)           |
S-Boxes           |  input 4 bits, output 2 bits |  input 6 bits, output 4 bits |
"""

class DESCipher(Cipher):

    S1 = [[14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7], [0,15,7,4,14,2,13,1,10,6,12,11,9,5,3,8], [4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0], [15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13]]
    S2 = [[15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10], [3,13,4,7,15,2,8,14,12,0,1,10,6,9,11,5], [0,14,7,11,10,4,13,1,5,8,12,6,9,3,2,15], [13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9]]
    S3 = [[10,0,9,14,6,3,15,5,1,13,12,7,11,4,2,8], [13,7,0,9,3,4,6,10,2,8,5,14,12,11,15,1], [13,6,4,9,8,15,3,0,11,1,2,12,5,10,14,7], [1,10,13,0,6,9,8,7,4,15,14,3,11,5,2,12]]
    S4 = [[7,13,14,3,0,6,9,10,1,2,8,5,11,12,4,15], [13,8,11,5,6,15,0,3,4,7,2,12,1,10,14,9], [10,6,9,0,12,11,7,13,15,1,3,14,5,2,8,4], [3,15,0,6,10,1,13,8,9,4,5,11,12,7,2,14]]
    S5 = [[2,12,4,1,7,10,11,6,8,5,3,15,13,0,14,9], [14,11,2,12,4,7,13,1,5,0,15,10,3,9,8,6], [4,2,1,11,10,13,7,8,15,9,12,5,6,3,0,14], [11,8,12,7,1,14,2,13,6,15,0,9,10,4,5,3]]
    S6 = [[12,1,10,15,9,2,6,8,0,13,3,4,14,7,5,11], [10,15,4,2,7,12,9,5,6,1,13,14,0,11,3,8], [9,14,15,5,2,8,12,3,7,0,4,10,1,13,11,6], [4,3,2,12,9,5,15,10,11,14,1,7,6,0,8,13]]
    S7 = [[4,11,2,14,15,0,8,13,3,12,9,7,5,10,6,1], [13,0,11,7,4,9,1,10,14,3,5,12,2,15,8,6], [1,4,11,13,12,3,7,14,10,15,6,8,0,5,9,2], [6,11,13,8,1,4,10,7,9,5,0,15,14,2,3,12]]
    S8 = [[13,2,8,4,6,15,11,1,10,9,3,14,5,0,12,7], [1,15,13,8,10,3,7,4,12,5,6,11,0,14,9,2], [7,11,4,1,9,12,14,2,0,6,10,13,15,3,5,8], [2,1,14,7,4,10,8,13,15,12,9,0,3,5,6,11]]
    SM = [S1, S2, S3, S4, S5, S6, S7, S8]

    @staticmethod
    def tobits(s):
        result = []
        for c in s:
            bits = bin(ord(c))[2:]
            bits = '00000000'[len(bits):] + bits
            result.extend([int(b) for b in bits])
        return result

    @staticmethod
    def frombits(bits):
        chars = []
        #print(len(bits) / 8)
        for b in range(int(len(bits) / 8)):
            byte = bits[b*8:(b+1)*8]
            chars.append(chr(int(''.join([str(bit) for bit in byte]), 2)))
        return ''.join(chars)

    @staticmethod
    def inv(perm):
        inverse = [0] * len(perm)
        for i, p in enumerate(perm):
            #print(i, p)
            inverse[p] = i
        return inverse

    @staticmethod
    def generatePermutation(length):
        range_ = np.array(list(range(length)), dtype = int)
        perm = list(np.random.permutation(range_, ))
        for i in range(len(perm)):
            perm[i] = int(perm[i])
        return perm

    @staticmethod
    def applyPermutation(permutation, block, shift = False):
        #print("Apply permutation: ")
        #print(permutation)
        if shift: move = 1
        else: move = 0
        return [block[i-move] for i in permutation]

    @staticmethod
    def computeXOR(a: List[int], b: List[int]):
        xor_list = list()
        if len(a) != len(b): raise Exception("Can't compute XOR over lists of different size.")
        for i in range(len(a)):
            bit_a = a[i]
            bit_b = b[i]
            result = int(bool(bit_a) != bool(bit_b))
            xor_list.append(result)
        return xor_list

    def __init__(self, key = None, mode = "ebc"):
        """
        DES is a 16-round Feistel cipher having block length 64:
        it encrypts a plaintext bistring x using a 56-bit key, K, obtaining a 
        ciphertext bistring (of length 64).
        """
        super().__init__()
        self.BLOCK_LENGTH = 64
        self.KEY_LENGTH = 56
        self.SUBKEY_LENGTH = 48
        self.ROUNDS = 16
        self.bit_selection_table = [32, 1, 2, 3, 4, 5, 4, 5, 6, 7, 8, 9, 8, 
        9, 10, 11, 12, 13, 12, 13, 14, 15, 16, 17, 16, 17, 18, 19, 
        20, 21, 20, 21, 22, 23, 24, 25, 24, 25, 26, 27, 28, 29, 28, 
        29, 30, 31, 32, 1]
        self.permutation_table = [16, 7, 20, 21, 29, 12, 28, 17, 1, 15, 23, 26, 5, 18, 31,
                       10, 2, 8, 24, 14, 32, 27, 3, 9, 19, 13, 30, 6, 22, 11, 4, 25]

        self.key = self.iniKey(key)
        self.permutation = DESCipher.generatePermutation(self.BLOCK_LENGTH)
        self.schedule = self.generateKeySchedule()
        self.mode = mode

    def setEncryptionMode(self, mode):
        self.mode = mode
    
    def setInitialPermutation(self, permutation):
        self.permutation = permutation

    def funcPermutation(self, block):
        """
        The Permutation P is as follows:
        It is apply over C1.C2. ... C7.C8
        32 bits block.
        """
        #print(len(permutation))
        return DESCipher.applyPermutation(self.permutation_table, block, shift = True)

    def expandBlock(self, block):
        """
        E(A) consists of the 32 bits from A, permuted in a certain way, with 16 of the bits appearing twice.
        It returns a block of 48 bits.
        """
        expanded_block = list()
        for i in range(len(self.bit_selection_table)):
            bit_index = self.bit_selection_table[i]
            expanded_block.append(block[bit_index - 1])
        return expanded_block

    def getBlocks(self, bits):
        num = round((len(bits) / self.BLOCK_LENGTH))
        blocks = list()
        for i in range(num):
            blocks.append(bits[self.BLOCK_LENGTH*i:self.BLOCK_LENGTH*(i+1)])
        for j in range(num):
            if len(blocks[j]) != self.BLOCK_LENGTH:
                diff = self.BLOCK_LENGTH - len(blocks[j])
                blocks[j] = blocks[j] + [0] * diff
        return blocks

    def roundFunction(self, A, J):
        ea = self.expandBlock(A)
        B = DESCipher.computeXOR(ea, J)
        #print("print bis")
        concatenation = ""

        # Iterate over 8 sub-blocks of length 6. (8 x 6 = 48)
        for i in range(8):        # 2
            bj = B[i*6 : 6 * (i+1)]   # 4
            b1b6 = str(bj[0]) + str(bj[5])
            b2tob5 = "".join([str(x) for x in bj[1: 5]])
            y = int(b1b6, 2)
            x = int(b2tob5, 2)
            matrix = DESCipher.SM[i]
            number = format(matrix[y][x], "b")
            diff = 4 - len(number)      # 2
            number = ("0" * diff) + number
            concatenation += number
            #print("number: ", number, type(number))
        C = list()
        for s in concatenation: 
            C.append(int(s))
        #print(len(C))
        return self.funcPermutation(C)

    def validKey(self, key): 
        if len(key) != self.KEY_LENGTH:
            return False
        for bit in key:
            if bit != 0 and bit != 1:
                return False
        return True
    
    def generateRandomKey(self):
        key = np.random.binomial(n = 1, p = 0.5, size=[self.KEY_LENGTH])
        return list(key)

    def generateKeySchedule(self):
        """
        The key schedule consists of 48-bit round keys that are derived from the 56-bit key, K.
        Each K^i is a certain permuted selection of bits from K.
        """
        schedule = list()
        for i in range(self.ROUNDS):
            key_copy = copy.deepcopy(self.key)
            for i in range(self.KEY_LENGTH - self.SUBKEY_LENGTH):
                rand_num = random.randint(0, self.KEY_LENGTH - i - 1)
                del key_copy[rand_num]
            perm = self.generatePermutation(self.SUBKEY_LENGTH)
            key_permuted = self.applyPermutation(perm, key_copy)
            schedule.append(key_permuted)
        return schedule
        
    def applyRounds(self, L, R):
        
        for i in range(self.ROUNDS):
            f_RK = self.roundFunction(R, self.schedule[i])
            new_R = DESCipher.computeXOR(L, f_RK)
            new_L = R
        return new_L, new_R

    def encode(self, cleartext: str):
        ### Encryption Modes.
        ### https://es.wikipedia.org/wiki/Modos_de_operaci%C3%B3n_de_una_unidad_de_cifrado_por_bloques#Modo_ECB_(Electronic_codebook)


        #print(self.schedule)
        # Get bits and blocks.
        bits = DESCipher.tobits(cleartext)
        blocks = self.getBlocks(bits)
        current_cleartext = None
        current_block = None

        # Encode text.
        ciphertext = ""
        for i in range(len(blocks)):

            current_cleartext = blocks[i]
            if self.mode != "ecb":
                blocks[i] = DESCipher.applyPermutation(self.permutation, blocks[i])

            if current_block is not None:
                if self.mode == "cbc":
                    blocks[i] = DESCipher.computeXOR(blocks[i], current_block)
                elif self.mode == "pcbc":
                    xor_block = DESCipher.computeXOR(current_cleartext, blocks[i])
                    blocks[i] = DESCipher.computeXOR(blocks[i], xor_block)

            L = blocks[i][0: int(self.BLOCK_LENGTH / 2)]
            R = blocks[i][int(self.BLOCK_LENGTH / 2): self.BLOCK_LENGTH]
            L, R = self.applyRounds(L, R) # 16 rounds.
            blocks[i] = R + L

            if self.mode != "ecb":
                blocks[i] = DESCipher.applyPermutation(DESCipher.inv(self.permutation), blocks[i])

            current_block = blocks[i]
            ciphertext += DESCipher.frombits(blocks[i])

        return ciphertext, self.permutation, self.schedule

    def decode(self, permutation: List[int], schedule: List[List[int]], ciphertext: str):
        if permutation is not None:
            self.permutation = permutation
        if schedule is not None:
            self.schedule = schedule
        return self.encode(ciphertext)

    def imagToMat(self, image):
        image = Image.open(image)
        image = np.asarray(image)
        return image

    def encode_image(self, image, filename = "guru991.txt"):
        
        def list_int_to_str(list_: List[int]):
            new_list = list()
            for element in list_:
                new_list.append(str(element))
            return new_list

        def format_pixel(pixeles: List[int]):
            pixeles = list_int_to_str(pixeles)
            dicc = {
                "0": "cero",
                "1": "uno", 
                "2": "dos", 
                "3": "tres",
                "4": "cuatro", 
                "5": "cinco", 
                "6": "seis", 
                "7": "siete", 
                "8": "ocho", 
                "9": "nueve"
            }
            row_text = ""
            for pixel in pixeles:
                pixel_text = ""
                for number in pixel: 
                    pixel_text += (dicc[number] + "pi")
                row_text += pixel_text + "tao"
            return row_text
                

        f = open(filename,"w+")
        img = self.imagToMat(image)
        img = np.reshape(img, (3, img.shape[0], img.shape[1]))
        img = np.resize(img, (3, 2, 2))
        #img = img.convert("L")
        print(img.shape)
        #print(img.shape[1])
        #print()
        #import sys
        #sys.exit()
        
        for k in range(img.shape[0]):
            print("chnnale number: ", k)
            for i in range(img.shape[1]):
                print("row number: ", i)
                pixel = format_pixel(list(img[k][i, :]))
                #print(pixel)
                cpt, perm, sche = self.encode(pixel)
                print(cpt)
                print("---")
                print(type(cpt), type(cpt.encode("utf-8").hex() ))
                f.write("{cpt}".format(cpt = cpt.encode("utf-8").hex()))
                f.write("\n\n")
            f.write("new_channel")
            f.write("\n\n")
        f.close()
        return perm, sche

    def decode_image(self, filename):
        with open(filename) as file:
            lines = file.readlines()
            
            #lines = [line.rstrip() for line in lines]
        print(lines[0])
        
        print("*****8")
        row0 = bytes.fromhex(lines[0]).decode("utf-8")
        row1 = bytes.fromhex(lines[1]).decode("utf-8")
        print("row: ")
        print(row0)
        print("row: ")
        print(row1)
        #print(r)
        result = cipher.decode(self.permutation, self.schedule, row0)
        print("result!")
        print(result)
        
class SDESCipher(DESCipher):

    # Reference: https://www.geeksforgeeks.org/simplified-data-encryption-standard-set-2/
    # https://www.geeksforgeeks.org/simplified-data-encryption-standard-key-generation/#:~:text=Simplified%20Data%20Encryption%20Standard%20(S,understanding%20DES%20would%20become%20simpler.
    # https://www.geeksforgeeks.org/simplified-data-encryption-standard-set-2/
    S1 = [[1,0,3,2], [3,2,1,0], [0,2,1,3], [3,1,3,2]]
    S2 = [[0,1,2,3], [2,0,1,3], [3,0,1,0], [2,1,0,3]]
    SM = [S1, S2]

    def __init__(self, key = None):
        """
        SDES: Simplified DES.
        """
        self.BLOCK_LENGTH = 8
        self.KEY_LENGTH = 10
        self.SUBKEY_LENGTH = 8
        self.ROUNDS = 2
        self.bit_selection_table = [4, 1, 2, 3, 2, 3, 4, 1]
        self.permutation_table = [2,4,3,1]

        self.key = self.iniKey(key)
        self.permutation = DESCipher.generatePermutation(self.BLOCK_LENGTH)
        self.schedule = self.generateKeySchedule()
        #print("permutation: ", self.permutation)
        #print("key: ", self.key)
        #print("schedule: ", self.schedule)

    def roundFunction(self, A, J):
        ea = self.expandBlock(A)
        B = DESCipher.computeXOR(ea, J)
        #print("print bis")
        concatenation = ""

        # Iterate over 2 sub-blocks of length 4. (2 x 4 = 8)
        for i in range(2):        
            bj = B[i*4 : 4 * (i+1)]   
            b1b6 = str(bj[0]) + str(bj[3])
            b2tob5 = "".join([str(x) for x in bj[1: 3]])
            y = int(b1b6, 2)
            x = int(b2tob5, 2)
            matrix = SDESCipher.SM[i]
            number = format(matrix[y][x], "b")
            diff = 2 - len(number)      
            number = ("0" * diff) + number
            concatenation += number

        C = list()
        for s in concatenation: 
            C.append(int(s))
        #print(len(C))
        return self.funcPermutation(C)

class TripleDESCipher(Cipher):

    def __init__(self, mode = "ebc"):
        super().__init__()
        self.des1 = DESCipher()
        self.des2 = DESCipher()
        self.des3 = DESCipher()

    def generateRandomKey(self):
        return self.des1.generateRandomKey()

    def setEncryptionMode(self, mode):
        self.des1.setEncryptionMode(mode)
        self.des2.setEncryptionMode(mode)
        self.des3.setEncryptionMode(mode)

    def configDES(self):
        key2 = [1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0] 
        schedule2 = [[1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1], [1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1], [1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0], [0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1], [0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1], [0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0], [0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1], [1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1], [1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1], [0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1], [0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0], [1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1], [0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0], [1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0], [0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0], [1, 0, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]]
        perm2 = [28, 6, 24, 42, 23, 46, 55, 5, 18, 11, 41, 3, 7, 47, 27, 37, 22, 14, 40, 39, 48, 19, 29, 9, 52, 54, 1, 17, 21, 13, 59, 38, 43, 51, 57, 60, 61, 25, 35, 34, 36, 63, 33, 15, 20, 32, 31, 16, 56, 2, 44, 45, 8, 26, 4, 10, 49, 0, 30, 50, 58, 12, 62, 53]
        self.des2.key = key2
        self.des2.schedule = schedule2
        self.des2.permutation = perm2

        key3 = [1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0]
        schedule3 = [[0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0], [1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0], [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1], [1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0], [1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0], [1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0], [0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0], [0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0], [1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0], [0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0], [0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1], [0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0], [0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0], [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0], [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1], [0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0]]
        perm3 = [24, 20, 36, 17, 7, 32, 12, 3, 44, 48, 11, 50, 2, 0, 18, 15, 39, 51, 4, 29, 54, 37, 30, 56, 23, 46, 58, 27, 21, 6, 61, 45, 10, 47, 34, 49, 8, 59, 33, 22, 25, 1, 14, 5, 57, 53, 52, 19, 40, 63, 42, 9, 28, 43, 35, 16, 38, 41, 13, 31, 26, 62, 55, 60]
        self.des3.key = key3
        self.des3.schedule = schedule3
        self.des3.permutation = perm3

    def encode(self, cleartext):
        self.configDES()
        ciphertext, perm1, schedule1 = self.des1.encode(cleartext)
        ciphertext, perm2, schedule2  = self.des2.encode(ciphertext)
        ciphertext, perm3, schedule3  = self.des3.encode(ciphertext)
        return ciphertext, perm1, schedule1 

    def decode(self, permutation: List[int], schedule: List[List[int]], ciphertext):
        self.configDES()
        if permutation is not None:
            self.des1.permutation = permutation
        if schedule is not None:
            self.des1.schedule = schedule   

        cleartext1 = self.des1.decode(None, None, ciphertext)
        cleartext2 = self.des2.decode(None, None, cleartext1[0])
        cleartext3 = self.des3.decode(None, None, cleartext2[0])
        return cleartext3[0], cleartext1[1], cleartext1[2]

def encrypt_image(key, iv, encryptionMode: str, image, filename: str):
    from Crypto import Random
    #key = Random.new().read(DES.key_size)
    #iv = Random.new().read(DES.block_size)
    def format_image(img):
        # Pad zero rows in case number of bytes is not a multiple of 16 (just an example - there are many options for padding)
        if img.size % 16 > 0:
            row = img.shape[0]
            pad = 16 - (row % 16)  # Number of rows to pad (4 rows)
            img = np.pad(img, ((0, pad), (0, 0), (0, 0)))  # Pad rows at the bottom  - new shape is (304, 451, 3) - 411312 bytes.
            img[-1, -1, 0] = pad  # Store the pad value in the last element
        return img

    # Read image
    img = Image.open(image)
    img = np.asarray(img)

    img = format_image(img)
    img_bytes = img.tobytes()  # Convert NumPy array to sequence of bytes (411312 bytes)
    if encryptionMode == "cbc" or encryptionMode == "pcbc":
        enc_img_bytes = DES.new(key, DES.MODE_CBC, iv).encrypt(img_bytes)  # Encrypt the array of bytes.
    elif encryptionMode == "ecb":
        enc_img_bytes = DES.new(key, DES.MODE_ECB, iv).encrypt(img_bytes)  # Encrypt the array of bytes..
    else:
        enc_img_bytes = DES.new(key, DES.MODE_ECB).encrypt(img_bytes)
    # Convert the encrypted buffer to NumPy array and reshape to the shape of the padded image (304, 451, 3)
    enc_img = np.frombuffer(enc_img_bytes, np.uint8).reshape(img.shape)

    # Save image
    enc_img = Image.fromarray(enc_img.astype('uint8'), 'RGB')
    enc_img.save(filename)
    return True

def decrypt_image(key, iv, encryptionMode: str, image, filename: str):
    from Crypto import Random
    #key = Random.new().read(DES.key_size)
    #iv = Random.new().read(DES.block_size)

    # Read image
    enc_img = Image.open(image)
    enc_img = np.asarray(enc_img)

    if encryptionMode == "cbc" or encryptionMode == "pcbc":
        dec_img_bytes = DES.new(key, DES.MODE_CBC, iv).decrypt(enc_img.tobytes())
    elif encryptionMode == "ecb":
        dec_img_bytes = DES.new(key, DES.MODE_ECB, iv).decrypt(enc_img.tobytes())
    else:
        dec_img_bytes = DES.new(key, DES.MODE_ECB).decrypt(enc_img.tobytes())

    dec_img = np.frombuffer(dec_img_bytes, np.uint8).reshape(enc_img.shape) # The shape of the encrypted and decrypted image is the same (304, 451, 3)
    pad = int(dec_img[-1, -1, 0])  # Get the stored padding value
    dec_img = dec_img[0:-pad, :, :].copy()  # Remove the padding rows, new shape is (300, 451, 3)
    
    # Save image
    dec_img = Image.fromarray(dec_img.astype('uint8'), 'RGB')
    dec_img.save(filename)

    return True

if __name__ == '__main__':

    url = "32x32.jpg"
    cipher = DESCipher(mode = "pcbc")
    print("key")
    print(cipher.key)
    print("schedule")
    print(cipher.schedule)
    print("initial perm")
    print(cipher.permutation)
    #txt, perm, sche = cipher.encode("encriptar")
    #print(txt)
    #txt, perm, sche = cipher.decode(perm, sche, txt)
    #print(txt)
    #cipher.encode_image(url, "../images/guru991.txt")
    #file = "../images/guru991.txt"
    #print("DESCRYOT IAGE")
    #cipher.decode_image(file)
    """
    cleartext = "holamundoholamundoholaxxawde"
    cipher = DESCipher()
    print("cleartext: ")
    print(cleartext)
    res = cipher.encode(cleartext)
    print("encode:")
    print(res)
    res2 = cipher.encode(res)
    print("decode:")
    print(res2)
    """
    """
    cleartext = "holamundoholamundoholaxxawde"
    cipher = DESCipher()
    print("cleartext: ")
    print(cleartext)
    res = cipher.encode(cleartext)[0]
    schedule = cipher.schedule

    cipher = DESCipher()
    print("encode:")
    print(res)
    cipher.schedule = schedule
    res2 = cipher.decode(None, res)[0]
    print("decode:")
    print(res2)
    """

  
    #print(len(res[1]))
    #print("from bits")
    #print(DESCipher.frombits(res))

    #cipher.generateKeySchedule()
    #print(DESCipher.frombits(res[1]))
    #print(permutation)
    #print(cipher.schedule)

    #test = [1, 2, 3, 4, 5]
    #perm = [2,0,4,3,1]#DESCipher.generatePermutation(len(test))
    #inv_perm = DESCipher.inv(perm)
    #print(perm)
    #print(inv_perm)
    #print("init: ", test)
    #test = DESCipher.applyPermutation(perm, test)
    #print("after application: ", test)
    #test = DESCipher.applyPermutation(inv_perm, test)
    #print("revert application: ", test)
