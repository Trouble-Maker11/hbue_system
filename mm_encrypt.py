import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5


def rsa_encrypt(public_key_json, plaintext):
    """
    使用 RSA 公钥（PKCS#1 v1.5 填充）对明文进行加密。

    参数:
      public_key_json: dict，包含两个字段：
          - "modulus": RSA 模数，Base64 编码字符串
          - "exponent": RSA 公钥指数，Base64 编码字符串
      plaintext: 需要加密的字符串（如密码）

    返回:
      加密后的密文，Base64 编码字符串
    """
    # 从 JSON 中获取 modulus 和 exponent 的 Base64 编码字符串
    modulus_b64 = public_key_json.get("modulus")
    exponent_b64 = public_key_json.get("exponent")
    if not modulus_b64 or not exponent_b64:
        raise ValueError("公钥 JSON 中缺少 modulus 或 exponent 字段")

    # 将 Base64 编码的字符串解码成 bytes
    modulus_bytes = base64.b64decode(modulus_b64)
    exponent_bytes = base64.b64decode(exponent_b64)

    # 将 bytes 转换成整数，注意使用大端字节序
    modulus_int = int.from_bytes(modulus_bytes, byteorder='big')
    exponent_int = int.from_bytes(exponent_bytes, byteorder='big')

    # 构造 RSA 公钥对象
    rsa_key = RSA.construct((modulus_int, exponent_int))

    # 使用 PKCS#1 v1.5 构造加密器
    cipher = PKCS1_v1_5.new(rsa_key)

    # 加密明文（需先编码为 utf-8 bytes）
    encrypted_bytes = cipher.encrypt(plaintext.encode('utf-8'))

    # 为了与 JS 代码中 hex2b64 的转换结果类似，这里将密文转换为 Base64 编码字符串返回
    encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')
    return encrypted_b64

