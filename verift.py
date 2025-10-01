import cv2
import os


def haha():
    # 导入背景 缺口图片
    img_a = cv2.imread('slider.png')
    img_b = cv2.imread('background.png')
    os.remove('slider.png')
    os.remove('background.png')
    x = 0
    """
        你需要自己写匹配缺口跟滑块的代码，然后将滑块要滑动的距离赋值给x
        有两种办法
        1. 其实教务系统的滑块验证码是固定的，也就那么几种搭配，你可以直接将值存为文件，到时候去识别然后匹配
        2. 用cv库先色转一下，然后再用轮廓匹配，就能得到要滑动的距离
        3. 机器训练，但是训练出来的模型会让打包后的文件变得很大， 但是如果你想练手，这是一个不错的选择 注：机器训练后的结果需要重写mt函数
        mt函数我为了模拟真人滑动的效果加入了抖动，你机器训练的结果已经包含了抖动，也包括了延迟！
    """
    return x


if __name__ == '__main__':
    haha()
