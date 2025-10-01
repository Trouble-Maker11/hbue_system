import base64
import json
import re
import time

from bs4 import BeautifulSoup

import config
import mm_encrypt
import verift
from utils import ef, mt


def get_key(user_data, password_data):
    """
        获取到公钥，再手动加密
    """
    key_url = 'http://端口/jwglxt/xtgl/login_getPublicKey.html'
    # 获取当前毫秒级时间戳
    current_time = int(time.time() * 1000)

    # 构造数据字典
    key_data = {
        "time": str(current_time + 428),  # 模拟稍后的时间戳
        "_": f"{current_time}",  # 当前时间戳
    }
    keys = config.session.get(url=key_url, headers=config.headers, data=key_data).json()
    # 将加密后的密文转换为 Base64 编码
    mm = mm_encrypt.rsa_encrypt(keys, password_data)
    login_url = 'http://端口/jwglxt/xtgl/login_slogin.html'
    login_header = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'connection': 'keep-alive',
        'referer': 'http://端口/jwglxt/xtgl/login_slogin.html',
        'host': '端口',
        'origin': 'http://端口',
        'content-length': '489',
        'proxy-connection': 'keep-alive',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
    }
    login_data = {
        'csrftoken': f"{config.csrf_token}",
        'language': 'zh_CN',
        'yhm': f'{user_data}',
        'mm': f"{mm}"
    }
    config.session.post(login_url, headers=login_header, data=login_data)
    # print("Response cookies:", resp.cookies)
    # print("Session cookies:", session.cookies.get_dict())


def login(user_param, password_param):
    """
    登录封装函数，传入用户名和密码完成整个登录流程，返回登录后的 session 对象。

    具体流程：
      1. 获取登录页，初始化 Cookie 及 CSRF token；
      2. 下载验证码（包含滑块与背景图片）；
      3. 破解验证码（获取滑块移动距离并模拟运动轨迹）；
      4. 获取公钥并对密码加密，然后发起登录请求。
    """

    # # 初始化登录页，获取 Cookie 和 csrftoken
    # get_cookie_1()
    # # 处理验证码
    # catch_captcha()
    # crack_captcha()
    # 获取公钥并登录
    get_key(user_param, password_param)
    return config.session


def get_cookie_1():
    url = 'http://端口/jwglxt/xtgl/login_slogin.html'
    resp = config.session.get(url, headers=config.headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    csrf_input = soup.find("input", {"id": "csrftoken", "name": "csrftoken"})

    base_token = csrf_input["value"].split(",")[0]
    config.csrf_token = f"{base_token},{base_token.replace('-', '')}"  # 抓包获取到的csrftoken有两种形式，需要修饰一下
    return resp.cookies.get('JSESSIONID')


def catch_captcha():
    # 先向这个url请求到滑块的id 再进行二次请求，得到二进制数据
    captcha_url = 'http://端口/jwglxt/zfcaptchaLogin'

    param = \
        {
            'type': 'refresh',
            'rtk': '52dc311e-7d2c-421a-927b-094fb07e9bc2',
            'time': f'{time.time() * 1000}',
            'instanceId': 'zfcaptchaLogin'
        }
    resp = config.session.get(captcha_url, headers=config.headers, params=param).json()
    slider_id = resp['mi']
    background_id = resp['si']
    imtk = resp['imtk']
    # 构造滑块以及背景请求
    slider_param = \
        {
            'type': 'image',
            'id': f'{slider_id}',
            'imtk': f'{imtk}',
            't': f'{time.time() * 1000}',
            'instanceId': 'zfcaptchaLogin'
        }
    background_param = \
        {
            'type': 'image',
            'id': f'{background_id}',
            'imtk': f'{imtk}',
            't': f'{time.time() * 1000}',
            'instanceId': 'zfcaptchaLogin'
        }
    slider_resp = config.session.get(url=captcha_url, headers=config.headers, params=slider_param)
    background_resp = config.session.get(url=captcha_url, headers=config.headers, params=background_param)
    with open('slider.png', 'wb') as f:
        f.write(slider_resp.content)
    with open('background.png', 'wb') as f:
        f.write(background_resp.content)


def crack_captcha():
    # 先下载验证码
    catch_captcha()
    zfcaptchaLogin_url = 'http://端口/jwglxt/zfcaptchaLogin'
    rtk_param = \
        {
            'type': 'resource',
            'instanceId': 'zfcaptchaLogin',
            'name': 'zfdun_captcha.js'
        }
    resp = config.session.get(url=zfcaptchaLogin_url, headers=config.headers, params=rtk_param).text
    # 定义匹配 rtk 的正则表达式
    pattern = r"rtk\s*[:=]\s*['\"]([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})['\"]"
    # 搜索匹配项
    match = re.search(pattern, resp)
    rtk = match.group(1)
    json_str = json.dumps(config.extend, separators=(',', ':'))
    # Base64 编码
    encoded_extend = base64.b64encode(json_str.encode("utf-8")).decode()
    captcha_data = \
        {
            'type': 'verify',
            'rtk': f'{rtk}',
            'time': f'{round(time.time() * 1000)}',
            'mt': ef(mt(verift.haha())),
            'instanceId': 'zfcaptchaLogin',
            'extend': f'{encoded_extend}'
        }
    # 将参数post到服务器就解决了验证码
    config.session.post(url=zfcaptchaLogin_url, data=captcha_data)


def preprocess_captcha():
    get_cookie_1()  # 初始化会话及CSRF令牌
    catch_captcha()  # 下载验证码素材
    crack_captcha()  # 破解滑块验证码
