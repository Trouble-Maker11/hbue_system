from auth import preprocess_captcha, login

if __name__ == "__main__":
    preprocess_captcha()
    user = input("请输入学号: ")
    password = input("请输入密码: ")
    login(user, password)

