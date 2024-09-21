from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from PIL import Image
from io import BytesIO
from datetime import datetime
import requests
from info import USERNAME, PASSWORD, TELEGRAPH_API_URL, OPENAI_API_URL, OPENAI_API_KEY
import json
import urllib
import http.client
# Edge驱动路径
edgedriver_path = r'G:\python\edgedriver_win64\msedgedriver.exe'
image_save_path = r'G:\python\demo\grammar\image'

# 配置Edge选项
edge_options = Options()
edge_options.add_argument("--start-maximized")  # 最大化浏览器窗口
edge_options.add_argument("--disable-blink-features=AutomationControlled")  # 禁用自动化控制

# 创建Edge浏览器实例
service = EdgeService(executable_path=edgedriver_path)
driver = webdriver.Edge(service=service, options=edge_options)

# 修改window.navigator.webdriver的值
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    '''
})

# 打开淘宝登录页面
driver.get("https://login.taobao.com/member/login.jhtml")

# 显式等待，确保元素加载完成
wait = WebDriverWait(driver, 20)
time.sleep(3)
# 输入用户名
username_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="fm-login-id"]')))
username_input.clear()
username_input.send_keys(USERNAME)
time.sleep(4)
# 输入密码
password_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="fm-login-password"]')))
password_input.clear()
password_input.send_keys(PASSWORD)

# 点击登录按钮
login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="fm-button fm-submit password-login"]')))
login_button.click()


time.sleep(20)  # 根据实际情况调整等待时间

# 打开HPOI页面
driver.get("https://hpoi.taobao.com/search.htm?spm=a1z10.1-c-s.w5003-21969173972.1.625b73e2oM9DSr&search=y&orderType=hotsell_desc&catId=1316826231&scene=taobao_shop")

# 滚动页面
driver.execute_script("window.scrollTo(0, 400);")
time.sleep(2)

# 截取指定区域
screenshot = driver.get_screenshot_as_png()
screenshot = Image.open(BytesIO(screenshot))

# 截取中央宽979px，长1206px的区域
left = (screenshot.width - 979) / 2
top = 400
right = left + 979
bottom = top + 1206
cropped_screenshot = screenshot.crop((left, top, right, bottom))

# 保存截图
current_time = datetime.now().strftime("%Y%m%d%H%M%S")
screenshot_filename = f"{current_time}.png"
screenshot_path = f"{image_save_path}\\{screenshot_filename}"
cropped_screenshot.save(screenshot_path)

# 上传截图
with open(screenshot_path, 'rb') as f:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.post(TELEGRAPH_API_URL, files={'file': f}, headers=headers)

# 打印响应内容以检查结构
print("响应内容:", response.json())

if response.status_code == 200:
    result = response.json()
    if isinstance(result, list) and len(result) > 0:
        image_url = "https://missuo.ru" + result[0]['src']
        print(f"图片链接: {image_url}")
    else:
        print("图片上传响应格式不正确")
        driver.quit()
        exit()
else:
    print("图片上传失败")
    driver.quit()
    exit()

# 调用GPT-4 API识别图片中的视频标题和UP主名字
payload = {
    "model": "gpt-4o",
    "max_tokens": 4096,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "分析这张图片，把每组商品的数据用json的形式输出来(商品标题，现在价格，以前价格，已售数量)"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                }
            ]
        }
    ]
}

headers = {
    'Authorization': f'Bearer {OPENAI_API_KEY}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Content-Type': 'application/json'
}

# 解析主机和路径
parsed_url = urllib.parse.urlparse(OPENAI_API_URL)
api_host = parsed_url.netloc
api_path = parsed_url.path

# 创建 HTTP 连接
conn = http.client.HTTPSConnection(api_host)

# 发送请求
conn.request("POST", api_path, json.dumps(payload), headers)

# 获取响应
res = conn.getresponse()
data = res.read()

# 处理响应
if res.status == 200:
    result = json.loads(data.decode("utf-8"))
    print("API调用成功，响应内容：")
    print(json.dumps(result, indent=2, ensure_ascii=False))
else:
    print(f"API调用失败，状态码：{res.status}")
    print("响应内容：")
    print(data.decode("utf-8"))

# 退出浏览器
driver.quit()

