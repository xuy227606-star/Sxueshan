import os
import base64
import urllib.request
from pathlib import Path

import yaml


# =========================
# 机场订阅
# =========================

SUB_URL = os.environ.get("XUESHAN_SUB_URL")

if not SUB_URL:
    raise RuntimeError("没有找到 XUESHAN_SUB_URL")


def get_subscription(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "clash.meta"}
    )

    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()

    text = data.decode("utf-8", errors="replace").strip()

    # 直接就是 Clash / Mihomo YAML
    if "proxies:" in text:
        return text

    # 尝试 Base64
    try:
        decoded = base64.b64decode(
            text + "=" * (-len(text) % 4)
        ).decode("utf-8", errors="replace").strip()

        if "proxies:" in decoded:
            return decoded

    except Exception:
        pass

    raise RuntimeError(
        "机场订阅不是 Clash/Mihomo YAML 或 Base64 YAML"
    )


# =========================
# 动态家宽地区
# =========================

REGIONS = [
    ("🇭🇰 香港动态家宽",
     r"(?i)(🇭🇰|香港).*(动态.*家宽|家宽.*动态)"),

    ("🇹🇼 台湾动态家宽",
     r"(?i)(🇹🇼|台湾).*(动态.*家宽|家宽.*动态)"),

    ("🇯🇵 日本动态家宽",
     r"(?i)(🇯🇵|日本).*(动态.*家宽|家宽.*动态)"),

    ("🇸🇬 新加坡动态家宽",
     r"(?i)(🇸🇬|新加坡|狮城).*(动态.*家宽|家宽.*动态)"),

    ("🇰🇷 韩国动态家宽",
     r"(?i)(🇰🇷|韩国).*(动态.*家宽|家宽.*动态)"),

    ("🇺🇸 美国动态家宽",
     r"(?i)(🇺🇸|美国|USA|US).*(动态.*家宽|家宽.*动态)"),

    ("🇨🇦 加拿大动态家宽",
     r"(?i)(🇨🇦|加拿大|Canada).*(动态.*家宽|家宽.*动态)"),

    ("🇬🇧 英国动态家宽",
     r"(?i)(🇬🇧|英国|UK|United Kingdom).*(动态.*家宽|家宽.*动态)"),

    ("🇩🇪 德国动态家宽",
     r"(?i)(🇩🇪|德国|Germany).*(动态.*家宽|家宽.*动态)"),

    ("🇫🇷 法国动态家宽",
     r"(?i)(🇫🇷|法国|France).*(动态.*家宽|家宽.*动态)"),

    ("🇳🇱 荷兰动态家宽",
     r"(?i)(🇳🇱|荷兰|Netherlands).*(动态.*家宽|家宽.*动态)"),

    ("🇦🇺 澳大利亚动态家宽",
     r"(?i)(🇦🇺|澳大利亚|澳洲|Australia).*(动态.*家宽|家宽.*动态)")
]


# =========================
# Google / Gemini
# =========================

AI_RULES = [
    "DOMAIN-SUFFIX,gemini.google.com,Google & AI",
    "DOMAIN-SUFFIX,generativelanguage.googleapis.com,Google & AI",
    "DOMAIN-SUFFIX,ai.google.dev,Google & AI",
    "DOMAIN-SUFFIX,aistudio.google.com,Google & AI"
]


# =========================
# 生成配置
# =========================

def main():

    print("正在获取机场订阅...")

    config = yaml.safe_load(
        get_subscription(SUB_URL)
    )

    if not isinstance(config, dict):
        raise RuntimeError("订阅解析失败")

    if not isinstance(config.get("proxies"), list):
        raise RuntimeError("订阅中没有 proxies")

    print(
        "原节点数量:",
        len(config["proxies"])
