import requests

API_URL = "Your URL"
TOKEN = "Your token"
SHORT_KLINE_IMAGE_PATH = "short_kline.png"
LONG_KLINE_IMAGE_PATH = "long_kline.png"
COMPANY_NAME = "英伟达"
LAST_DATE = "2025-10-31"


def call_kline_api_correct_url():
    request_data = {
        # kline_image：短期K线图，使用本地图片Base64编码
        "kline_image": {
            "type": "file",
            "file_type": "image",
            "url": SHORT_KLINE_IMAGE_PATH,
            "description": "上传的短期K线图图片（用于分析当前趋势和短期结构）",
            "title": "File"
        },
        # kline_image_long：长期K线图，使用本地图片Base64编码
        "kline_image_long": {
            "type": "file",
            "file_type": "image",
            "url": LONG_KLINE_IMAGE_PATH,
            "description": "上传的长期K线图图片（用于分析长期趋势和战略方向）",
            "title": "File"
        },
        # 你的业务参数，完全保留
        "company_name": COMPANY_NAME,
        "last_date": LAST_DATE
    }

    # 唯一合法的请求头，必须加
    headers = {
        "Content-Type": "application/json",
        "Connection": "keep-alive",
        "Expect": "100-continue",
        "Authorization": "Bearer " + TOKEN
    }

    try:
        response = requests.post(url=API_URL, json=request_data, headers=headers, timeout=None)
        result = response.json()
        print("✅ 接口调用成功，返回结果：")
        print(result)
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ 接口调用失败：{e}")
        return None


if __name__ == "__main__":
    call_kline_api_correct_url()
