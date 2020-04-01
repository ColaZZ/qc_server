import base64
import json
from Crypto.Cipher import AES

class WXBizDataCrypt:
    def __init__(self, appId, sessionKey):
        self.appId = appId
        self.sessionKey = sessionKey

    def decrypt(self, encryptedData, iv):
        # base64 decode
        sessionKey = base64.b64decode(self.encode(self.sessionKey))
        encryptedData = base64.b64decode(self.encode(encryptedData))
        iv = base64.b64decode(self.encode(iv))

        cipher = AES.new(sessionKey, AES.MODE_CBC, iv)

        decrypted = json.loads(self._unpad(cipher.decrypt(encryptedData)))

        if decrypted['watermark']['appid'] != self.appId:
            raise Exception('Invalid Buffer')

        return decrypted

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]

    def encode(self, strg):
        lens = len(strg)
        lenx = lens - (lens % 4 if lens % 4 else 4)
        try:
            result = base64.decodebytes(strg[:lenx])
        except:
            result = ""

        return result