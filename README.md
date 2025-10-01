# 教务系统登录加密流程详解

## 概述

教务系统（地址：http://端口/jwglxt）的登录加密流程。该系统采用了多层安全机制，包括CSRF令牌、滑块验证码和RSA密码加密。

------

## 一、前期准备：获取CSRF令牌

### 1.1 CSRF令牌的作用

CSRF（跨站请求伪造）令牌是防止恶意攻击的重要安全机制。该令牌在整个登录流程中都会用到，是一个**全局变量**。

### 1.2 获取方式

访问登录页面，从HTML源码中提取CSRF令牌：

```python
def get_cookie_1():
    url = 'http://端口/jwglxt/xtgl/login_slogin.html'
    resp = config.session.get(url, headers=config.headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # 从页面中查找id为csrftoken的input标签
    csrf_input = soup.find("input", {"id": "csrftoken", "name": "csrftoken"})
    
    # 提取并处理token值
    base_token = csrf_input["value"].split(",")[0]
    # 注意：系统要求两种形式的token组合
    config.csrf_token = f"{base_token},{base_token.replace('-', '')}"
    
    return resp.cookies.get('JSESSIONID')
```

**关键点：**

- CSRF令牌从登录页面的隐藏input标签中获取
- 需要对原始token进行格式处理：`原始token,去除横杠的token`
- 同时获取JSESSIONID cookie，维持会话状态

------

## 二、滑块验证码处理

### 2.1 验证码流程概述

系统使用滑块验证码防止自动化登录，需要经过三个步骤：

1. 获取验证码ID和临时令牌
2. 下载滑块和背景图片
3. 破解并提交验证结果

### 2.2 步骤一：获取验证码元数据

```python
def catch_captcha():
    captcha_url = 'http://端口/jwglxt/zfcaptchaLogin'
    
    # 请求验证码初始化接口
    param = {
        'type': 'refresh',
        'rtk': '自己获取',  # 固定值
        'time': f'{time.time() * 1000}',  # 毫秒级时间戳
        'instanceId': 'zfcaptchaLogin'
    }
    
    resp = config.session.get(captcha_url, headers=config.headers, params=param).json()
    
    # 获取三个关键参数
    slider_id = resp['mi']      # 滑块图片ID
    background_id = resp['si']   # 背景图片ID
    imtk = resp['imtk']          # 临时令牌（Image Token）
```

**返回的关键参数：**

- `mi`（slider_id）：滑块图片的唯一标识
- `si`（background_id）：背景图片的唯一标识
- `imtk`：本次验证码会话的临时令牌

### 2.3 步骤二：下载验证码图片

使用获取到的ID和imtk下载滑块和背景图片：

```python
    # 构造滑块图片请求参数
    slider_param = {
        'type': 'image',
        'id': f'{slider_id}',
        'imtk': f'{imtk}',
        't': f'{time.time() * 1000}',
        'instanceId': 'zfcaptchaLogin'
    }
    
    # 构造背景图片请求参数
    background_param = {
        'type': 'image',
        'id': f'{background_id}',
        'imtk': f'{imtk}',
        't': f'{time.time() * 1000}',
        'instanceId': 'zfcaptchaLogin'
    }
    
    # 下载图片二进制数据
    slider_resp = config.session.get(url=captcha_url, headers=config.headers, 
                                     params=slider_param)
    background_resp = config.session.get(url=captcha_url, headers=config.headers, 
                                         params=background_param)
    
    # 保存到本地进行破解
    with open('slider.png', 'wb') as f:
        f.write(slider_resp.content)
    with open('background.png', 'wb') as f:
        f.write(background_resp.content)
```

### 2.4 步骤三：破解并提交验证码

```python
def crack_captcha():
    # 先下载验证码图片
    catch_captcha()
    
    zfcaptchaLogin_url = 'http://端口/jwglxt/zfcaptchaLogin'
    
    # 获取动态rtk参数
    rtk_param = {
        'type': 'resource',
        'instanceId': 'zfcaptchaLogin',
        'name': 'zfdun_captcha.js'
    }
    resp = config.session.get(url=zfcaptchaLogin_url, headers=config.headers, 
                              params=rtk_param).text
    
    # 使用正则表达式从JS源码中提取rtk
    pattern = r"rtk\s*[:=]\s*['\"]([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})['\"]"
    match = re.search(pattern, resp)
    rtk = match.group(1)  # 动态获取的rtk
    
    # 准备extend参数（浏览器环境信息）
    json_str = json.dumps(config.extend, separators=(',', ':'))
    encoded_extend = base64.b64encode(json_str.encode("utf-8")).decode()
    
    # 构造验证请求
    captcha_data = {
        'type': 'verify',
        'rtk': f'{rtk}',  # 动态rtk
        'time': f'{round(time.time() * 1000)}',
        'mt': ef(mt(verift.haha())),  # 滑块移动轨迹（Base64编码）
        'instanceId': 'zfcaptchaLogin',
        'extend': f'{encoded_extend}'  # 浏览器环境信息（Base64编码）
    }
    
    # 提交验证
    config.session.post(url=zfcaptchaLogin_url, data=captcha_data)
```

**关键加密参数解析：**

1. **rtk参数（动态）**

   - 需要访问 `http://218.197.80.13/jwglxt/zfcaptchaLogin?type=resource&name=zfdun_captcha.js`
   - 从返回的JavaScript源码中用正则表达式提取
   - 格式：UUID形式（如 `52bc221e-7d2c-421a-927b-094fb07e9bc2`）

2. **mt参数（移动轨迹）**

   - 包含滑块移动的轨迹数据
   - 需要先计算滑块应移动的距离（通过图像识别算法）
   - 生成模拟人类操作的移动轨迹（加速-匀速-减速）
   - 最后对轨迹数据进行Base64编码

3. **extend参数（环境信息）**

   - 包含浏览器信息（User-Agent、appName等）
   - 将JSON对象转为字符串后Base64编码

   ```python
   extend = {
       "appName": "Netscape",
       "userAgent": "Mozilla/5.0 ...",
       "appVersion": "5.0 ..."
   }
   ```

------

## 三、密码加密与登录

### 3.1 RSA加密流程

教务系统采用**RSA公钥加密**方式保护密码传输安全。

#### 3.1.1 获取公钥

```python
def get_key(user_data, password_data):
    key_url = 'http://端口/jwglxt/xtgl/login_getPublicKey.html'
    
    # 获取当前毫秒级时间戳
    current_time = int(time.time() * 1000)
    
    # 构造请求参数
    key_data = {
        "time": str(current_time + 428),  # 模拟稍后的时间戳
        "_": f"{current_time}",            # 当前时间戳
    }
    
    # 请求获取公钥
    keys = config.session.get(url=key_url, headers=config.headers, 
                              data=key_data).json()
```

**返回的公钥格式：**

```json
{
    "modulus": "AJbxR4R+HXEi3BIxNwgG6DD63qXT+6lHYIfSSAcmVxlF...",  // Base64编码的模数
    "exponent": "AQAB"  // Base64编码的指数
}
```

#### 3.1.2 RSA加密实现

```python
def rsa_encrypt(public_key_json, plaintext):
    """
    使用 RSA 公钥（PKCS#1 v1.5 填充）对明文进行加密
    """
    # 1. 从JSON中提取模数和指数（Base64格式）
    modulus_b64 = public_key_json.get("modulus")
    exponent_b64 = public_key_json.get("exponent")
    
    # 2. Base64解码为字节
    modulus_bytes = base64.b64decode(modulus_b64)
    exponent_bytes = base64.b64decode(exponent_b64)
    
    # 3. 转换为整数（大端字节序）
    modulus_int = int.from_bytes(modulus_bytes, byteorder='big')
    exponent_int = int.from_bytes(exponent_bytes, byteorder='big')
    
    # 4. 构造RSA公钥对象
    rsa_key = RSA.construct((modulus_int, exponent_int))
    
    # 5. 使用PKCS#1 v1.5填充方式创建加密器
    cipher = PKCS1_v1_5.new(rsa_key)
    
    # 6. 加密密码（UTF-8编码）
    encrypted_bytes = cipher.encrypt(plaintext.encode('utf-8'))
    
    # 7. 转换为Base64编码字符串返回
    encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')
    return encrypted_b64
```

**加密步骤详解：**

1. **解码公钥**：将Base64编码的modulus和exponent解码为字节数组
2. **转换整数**：使用大端字节序将字节数组转为整数
3. **构造密钥**：使用PyCrypto库构造RSA公钥对象
4. **PKCS#1填充**：使用PKCS#1 v1.5填充标准（兼容JavaScript实现）
5. **加密并编码**：加密后转为Base64格式便于传输

### 3.2 提交登录请求

```python
    # 加密密码
    mm = mm_encrypt.rsa_encrypt(keys, password_data)
    
    login_url = 'http://端口/jwglxt/xtgl/login_slogin.html'
    
    # 构造登录请求头
    login_header = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9...',
        'content-type': 'application/x-www-form-urlencoded',
        'referer': 'http://218.197.80.13/jwglxt/xtgl/login_slogin.html',
        'origin': 'http://218.197.80.13',
        'user-agent': 'Mozilla/5.0 ...',
        # ... 其他请求头
    }
    
    # 构造登录表单数据
    login_data = {
        'csrftoken': f"{config.csrf_token}",  # 之前获取的CSRF令牌
        'language': 'zh_CN',
        'yhm': f'{user_data}',                 # 用户名（学号）
        'mm': f"{mm}"                          # RSA加密后的密码
    }
    
    # 发送POST请求完成登录
    config.session.post(login_url, headers=login_header, data=login_data)
```

------

## 四、完整登录流程总结

### 4.1 流程图

```
开始
  ↓
① 访问登录页获取CSRF令牌和Session Cookie
  ↓
② 请求验证码接口获取滑块ID、背景ID和imtk
  ↓
③ 下载滑块和背景图片到本地
  ↓
④ 图像识别计算滑块移动距离
  ↓
⑤ 从JS源码中提取动态rtk参数
  ↓
⑥ 生成移动轨迹并Base64编码（mt参数）
  ↓
⑦ 准备浏览器环境信息并Base64编码（extend参数）
  ↓
⑧ POST提交验证码验证请求
  ↓
⑨ 请求公钥接口获取RSA公钥（modulus和exponent）
  ↓
⑩ 使用公钥加密密码，得到Base64编码的密文
  ↓
⑪ POST提交登录表单（包含CSRF、用户名、加密密码）
  ↓
登录成功
```

### 4.2 核心代码调用

```python
def login(user_param, password_param):
    """
    完整登录流程封装
    """
    # 预处理：初始化Session、获取CSRF、处理验证码
    preprocess_captcha()
    
    # 获取公钥并加密密码，提交登录
    get_key(user_param, password_param)
    
    return config.session


def preprocess_captcha():
    """预处理验证码流程"""
    get_cookie_1()     # 获取CSRF令牌和Cookie
    catch_captcha()    # 下载验证码图片
    crack_captcha()    # 破解并提交验证码
```

------

## 五、关键技术要点

### 5.1 加密技术

| 加密类型       | 用途     | 算法                         |
| -------------- | -------- | ---------------------------- |
| **RSA加密**    | 密码保护 | PKCS#1 v1.5填充 + Base64编码 |
| **Base64编码** | 数据传输 | 用于mt、extend、mm等参数     |

### 5.2 动态参数

| 参数名         | 类型             | 获取方式       | 作用           |
| -------------- | ---------------- | -------------- | -------------- |
| **csrf_token** | 静态（单次会话） | HTML源码提取   | 防CSRF攻击     |
| **rtk**        | 动态             | JS源码正则匹配 | 验证码会话标识 |
| **imtk**       | 动态             | API返回        | 验证码图片令牌 |
| **time**       | 动态             | 毫秒时间戳     | 防重放攻击     |

### 5.3 注意事项

1. **Session管理**：使用`requests.Session()`维持Cookie状态，确保CSRF令牌和验证码状态有效
2. **时间戳精度**：所有时间戳使用毫秒级精度（`time.time() * 1000`）
3. **请求头完整性**：登录请求需要完整的浏览器请求头，特别是：
   - `Referer`：必须指向登录页
   - `Origin`：必须为系统域名
   - `User-Agent`：需与extend参数保持一致
4. **字符编码**：所有字符串操作使用UTF-8编码
5. **加密库选择**：
   - 使用`pycryptodome`库实现RSA加密
   - 如需减小打包体积，可自行实现RSA算法（不推荐，易出错）

------

## 六、依赖库

```python
# 必需的Python库
requests          # HTTP请求
beautifulsoup4    # HTML解析
pycryptodome      # RSA加密（Crypto库）
```



**免责声明**：本文档仅供学习交流使用，请勿用于非法用途。
