# -*- coding: utf-8 -*-
"""
@Function: xxx
"""
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
import base64

# 私钥
private_key = '''-----BEGIN RSA PRIVATE KEY-----
5353dfggd
-----END RSA PRIVATE KEY-----
'''

# 公钥
public_key = '''-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANeBpp2h87T10BskMkdTU4Wlp+9phEqjkSGXttUpBW1s42y0EyHySNfwH7bTEvMN83Dtb40iYxiRFbALdMDgmzsCAwEAAQ==
-----END PUBLIC KEY-----'''


def rsa_encrypt(message, pub_key=None):
    """校验RSA加密 使用公钥进行加密"""
    if not pub_key:
        pub_key = public_key
    cipher = Cipher_pkcs1_v1_5.new(RSA.importKey(pub_key))
    cipher_text = base64.b64encode(cipher.encrypt(message.encode())).decode()
    return cipher_text


def rsa_decrypt(text):
    """校验RSA加密 使用私钥进行解密"""
    cipher = Cipher_pkcs1_v1_5.new(RSA.importKey(public_key))
    retval = cipher.decrypt(base64.b64decode(text), 'ERROR').decode('utf-8')
    return retval


# print(rsa_decrypt('RnkYK/OD+74b2Xi26xJywsLRzqUgUd6so06YZn8WQ5nOCePJ2NClbsKnPBkXH2fllTwtykUZFAWIemc2Qi1PmA=='))
# print(rsa_encrypt('123'))

# print(rsa_encrypt('QFUFGOONAFNZ3LFZ'))
