#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
aes256.py
AES Everywhere - Cross Language Encryption Library
"""

import sys
import base64
from hashlib import md5
from Crypto import Random
from Crypto.Cipher import AES


class aes256:

    BLOCK_SIZE = 16
    KEY_LEN = 32
    IV_LEN = 16

    def encrypt(self, raw, passphrase):
        """
        Encrypt text with the passphrase
        @param raw: string Text to encrypt
        @param passphrase: string Passphrase
        @type raw: string
        @type passphrase: string
        @rtype: string
        """
        if raw is None:
            raw = ''
        salt = Random.new().read(8)
        key, iv = self.__derive_key_and_iv(passphrase, salt)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        raw_padded = self.__pkcs5_padding(raw)
        cipher_encrypted = cipher.encrypt(raw_padded)
        return base64.b64encode(b'Salted__' + salt + cipher_encrypted)

    def decrypt(self, enc, passphrase):
        """
        Decrypt encrypted text with the passphrase
        @param enc: string Text to decrypt
        @param passphrase: string Passphrase
        @type enc: string
        @type passphrase: string
        @rtype: string
        """
        ct = base64.b64decode(enc)
        salted = ct[:8]
        if salted != b'Salted__':
            return ""
        salt = ct[8:16]
        key, iv = self.__derive_key_and_iv(passphrase, salt)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return self.__pkcs5_trimming(cipher.decrypt(ct[16:]))

    def __pkcs5_padding(self, s):
        """
        Padding to blocksize according to PKCS #5
        calculates the number of missing chars to BLOCK_SIZE and pads with
        ord(number of missing chars)
        @see: http://www.di-mgt.com.au/cryptopad.html
        @param s: string Text to pad
        @type s: string
        @rtype: string
        """
        string_length = len(s.encode('utf-8'))
        s = s + (self.BLOCK_SIZE - string_length % self.BLOCK_SIZE) * \
            chr(self.BLOCK_SIZE - string_length % self.BLOCK_SIZE)
        if sys.version_info[0] == 2:
            return s
        return bytes(s, 'utf-8')

    def __pkcs5_trimming(self, s):
        """
        Trimming according to PKCS #5
        @param s: string Text to unpad
        @type s: string
        @rtype: string
        """
        if sys.version_info[0] == 2:
            return s[0:-ord(s[-1])]
        return s[0:-s[-1]]

    def __derive_key_and_iv(self, password, salt):
        """
        Derive key and iv
        @param password: string Password
        @param salt: string Salt
        @type password: string
        @type salt: string
        @rtype: string
        """
        d = d_i = b''
        while len(d) < self.KEY_LEN + self.IV_LEN:
            d_i = md5(d_i + password.encode('utf-8') + salt).digest()
            d += d_i
        return d[:self.KEY_LEN], d[self.KEY_LEN:self.KEY_LEN + self.IV_LEN]
