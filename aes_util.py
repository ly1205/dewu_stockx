# -*- coding:utf-8 -*-

from Crypto.Cipher import AES
import base64
import random
BS = AES.block_size


def pad(s):
    return s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
#定义 padding 即 填充 为PKCS7

def unpad(s):
    return s[0:-ord(s[-1])]


class prpcrypt():
    def __init__(self, key, iv):
        self.key = key
        self.iv = iv
        self.mode = AES.MODE_CBC

    def pkcs7padding(self, text):
        """

        明文使用PKCS7填充

        最终调用AES加密方法时，传入的是一个byte数组，要求是16的整数倍，因此需要对明文进行处理

        :param text: 待加密内容(明文)

        :return:

        """

        bs = AES.block_size  # 16
        length = len(text)
        bytes_length = len(bytes(text, encoding='utf-8'))
        # tips：utf-8编码时，英文占1个byte，而中文占3个byte
        padding_size = length if (bytes_length == length) else bytes_length
        padding = bs - padding_size % bs
        # tips：chr(padding)看与其它语言的约定，有的会使用'\0'
        padding_text = chr(padding) * padding
        return text + padding_text

    # AES的加密模式为CBC
    def encrypt(self, text):
        content_padding = self.pkcs7padding(text)
        cryptor = AES.new(self.key.encode('utf-8'), self.mode, self.iv.encode('utf-8'))
        aes_encode_bytes = cryptor.encrypt(content_padding.encode())
        # return base64.standard_b64encode(aes_encode_bytes).decode("utf-8")
        # return base64.b64encode(self.ciphertext).decode("utf-8")
        return ''.join(['%02X' % b for b in aes_encode_bytes])
        # return str(base64.b64encode(aes_encode_bytes), encoding='utf-8')

    def decrypt(self, text):
        cryptor = AES.new(self.key.encode('utf-8'), self.mode, self.iv.encode('utf-8'))
        de_text = base64.standard_b64decode(text)
        plain_text = cryptor.decrypt(de_text)
        st = str(plain_text.decode("utf-8")).rstrip('\0')
        out = unpad(st)
        return out

    @staticmethod
    def generate_aes_key(code_len=6):
        """
        随机生成48位aes密码
        """
        all_char = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        index = len(all_char) - 1
        code = ''
        for _ in range(code_len):
            num = random.randint(0, index)
            code += all_char[num]
        return code.upper()


# pc = prpcrypt('93JJl616ncPd5391', '93JJl616ncPd5391')  # 自己设定的密钥
# e = pc.encrypt("hello")  # 加密内容
# print(e)
# e = 'KOoUS1r0zvKirV49LIN9PiODk6b+87elmlmUx1F2E6abRM/E+r/Eu0uWv4TYQJakuX9dAAXvgkY9w1RNC7Htth0JPlEJ3DrG+ne/NqRV2XB/hGKF7ehE1IkkulbTLL7f8vM3aGCx7BgEIGeqOSbebRmbGf3n4VlA3SbRK7pxa1ttlPY7l5a1hOGFiIP7pPFpCWH7Df/WfIAy6US9enj8WbVj2hlIF84fGyleijHT/9DM1s8RhnSI9bUq3IwpwPU6qoPpM2rwYwFVMhfdkA9orz433EvZu2cazHLmfxjuJ/VpaGedxmH3iJkwjmSJ80x3h4/IP3I88/q9UsgI+YhaIJ9nfMx2FH63+QF5hOXKAylnMuwLMQGrsxeIsvRCubA4OpjYGYOVDNYgualhLZOq+3Nmrvlx8gvHk0ghIFK1GyjeFGrf0VVTmZiOwVyPGpo4sUptCtDAlx0H9L8BgsSa1I00WrS/9X78UWmfEgKnlGyGEEHK+Otz5ArAeaOl2ULVLQU/LjXwbqr5iF6JimUpkVZLGayHM3U4VWtfZHLXq1EdOJOYpaQP4aymhCwIMPSDSasGc1zFLP5ekpuFzsYnuiZwL9a4NsRIpncTFKz4jKiN0J6bENAwNMps89LOQZ6uGrnbtij1KkyXyS2iye6bPwPWSckNE75L00CgOHdpIsR/7CDSmip11W7EZiC9L2qz076sZKKsKM5I8fGL/gjgHA=='
# d = pc.decrypt(e)
# print("解密后%s" % d)
# okey = 'COEAZEOTLZQFUFGOONAFNZ3LFZWX9J5RIQHV21NSV4E7QVBP'
# aes_obj = prpcrypt('QFUFGOONAFNZ3LFZ', 'NZ3LFZWX9J5RIQHV')
# src_params = json.dumps({"sign": "263625efd36998fbd148d87d4c0139ac", "spuId": "1031816", "productSourceName": "", "propertyValueId": "", "sourceName": "shareDetail"})
# encrypt_params = aes_obj.encrypt(src_params)
# print(encrypt_params)
