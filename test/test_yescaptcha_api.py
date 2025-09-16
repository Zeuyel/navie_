"""
YesCaptcha API 手动测试脚本
用于验证API调用方法和响应格式
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import YESCAPTCHA_API_KEY, YESCAPTCHA_BASE_URL

import requests
import base64
import json

def test_api_connection():
    """测试API连接"""
    print("=== 测试API连接 ===")
    try:
        response = requests.get(f"{YESCAPTCHA_BASE_URL}/getBalance", 
                              params={"clientKey": YESCAPTCHA_API_KEY})
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"连接失败: {e}")
        return False

def url_to_base64(image_url):
    """从URL下载图片并转换为base64"""
    print(f"\n=== 从URL加载图片 ===")
    print(f"图片URL: {image_url}")

    try:
        # 下载图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()

        image_data = response.content
        print(f"图片大小: {len(image_data)} bytes")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")

        # 转换为base64
        image_base64 = base64.b64encode(image_data).decode()
        print(f"Base64长度: {len(image_base64)} 字符")

        # 根据content-type确定格式
        content_type = response.headers.get('content-type', '').lower()
        if 'png' in content_type:
            return f"data:image/png;base64,{image_base64}"
        elif 'jpeg' in content_type or 'jpg' in content_type:
            return f"data:image/jpeg;base64,{image_base64}"
        elif 'gif' in content_type:
            return f"data:image/gif;base64,{image_base64}"
        elif 'webp' in content_type:
            return f"data:image/webp;base64,{image_base64}"
        else:
            # 默认使用png格式
            return f"data:image/png;base64,{image_base64}"

    except requests.exceptions.RequestException as e:
        print(f"下载图片失败: {e}")
        return None
    except Exception as e:
        print(f"处理图片失败: {e}")
        return None

def load_test_image():
    """加载测试图片并转换为base64"""
    print("\n=== 加载测试图片 ===")

    # 方法1: 从URL加载
    image_url = input("请输入验证码图片URL (或按Enter跳过): ").strip()
    if image_url:
        return url_to_base64(image_url)

    # 方法2: 从本地文件加载
    print("尝试加载本地文件 test_captcha.png...")
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
# 构建图片文件的完整路径
    image_path = os.path.join(current_dir, 'test_captcha.png')
    try:
        with open( image_path, 'rb') as image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode()
            print(f"图片大小: {len(image_data)} bytes")
            print(f"Base64长度: {len(image_base64)} 字符")
            return f"data:image/png;base64,{image_base64}"
    except FileNotFoundError:
        print("未找到 test_captcha.png 文件")
        print("请提供验证码图片URL或将截图保存为 test_captcha.png")
        return None
    except Exception as e:
        print(f"加载图片失败: {e}")
        return None

def test_funcaptcha_api(image_base64, question):
    """测试FunCaptcha识别API"""
    print(f"\n=== 测试FunCaptcha API ===")
    print(f"问题: {question}")
    
    payload = {
        "clientKey": YESCAPTCHA_API_KEY,
        "task": {
            "type": "FunCaptchaClassification",
            "image": image_base64,
            "question": question
        }
    }
    
    try:
        print("发送请求...")
        response = requests.post(f"{YESCAPTCHA_BASE_URL}/createTask", 
                               json=payload, 
                               timeout=30)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get('errorId') == 0:
                solution = result.get('solution', {})
                objects = solution.get('objects', [])
                labels = solution.get('labels', [])
                
                print(f"\n=== 识别结果 ===")
                print(f"目标位置: {objects}")
                print(f"标签列表: {labels}")
                
                if objects:
                    target_index = objects[0]
                    print(f"应该点击第 {target_index + 1} 个位置 (索引: {target_index})")
                    if target_index < len(labels):
                        print(f"目标对象: {labels[target_index]}")
                
                return True
            else:
                print(f"API错误: {result}")
                return False
        else:
            print(f"HTTP错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def main():
    """主函数"""
    print("YesCaptcha API 手动测试")
    print("=" * 50)
    
    # 检查API密钥
    if not YESCAPTCHA_API_KEY or YESCAPTCHA_API_KEY == "your_api_key_here":
        print("错误: 请在 .env 文件中设置正确的 YESCAPTCHA_API_KEY")
        return
    
    print(f"API密钥: {YESCAPTCHA_API_KEY[:10]}...")
    print(f"API地址: {YESCAPTCHA_BASE_URL}")
    
    # 测试连接
    if not test_api_connection():
        print("API连接失败，请检查网络和密钥")
        return
    
    # 加载测试图片
    image_base64 = load_test_image()
    if not image_base64:
        print("无法加载测试图片，请准备验证码截图")
        return
    
    # 测试问题示例
    test_questions = [
        "Pick the bread",
        "Pick the penguin", 
        "Pick one square that shows two identical objects",
        "Pick the shadow with a different object silhouette"
    ]
    
    print(f"\n可用的测试问题:")
    for i, q in enumerate(test_questions, 1):
        print(f"{i}. {q}")
    
    # 让用户选择问题或输入自定义问题
    try:
        choice = input("\n请选择问题编号(1-4)或直接输入问题文本: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(test_questions):
            question = test_questions[int(choice) - 1]
        else:
            question = choice if choice else test_questions[0]
        
        # 测试API
        success = test_funcaptcha_api(image_base64, question)
        
        if success:
            print("\n✅ API测试成功!")
        else:
            print("\n❌ API测试失败!")
            
    except KeyboardInterrupt:
        print("\n用户取消测试")
    except Exception as e:
        print(f"\n测试过程出错: {e}")

if __name__ == "__main__":
    main()
