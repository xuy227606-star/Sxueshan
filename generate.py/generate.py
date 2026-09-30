import os
import base64
import urllib.request
from pathlib import Path

import yaml


# ============================================================
# 1. 从 GitHub Actions Secret 读取机场订阅
# ============================================================

SUB_URL = os.environ.get("XUESHAN_SUB_URL", "").strip()

if not SUB_URL:
    raise RuntimeError(
        "没有找到 XUESHAN_SUB_URL，请检查 GitHub Repository Secret。"
    )


# ============================================================
# 2. 下载机场订阅
# ============================================================

def fetch_subscription(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "clash.meta",
            "Accept": "*/*",
        },
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read()

    # 先尝试直接作为 UTF-8
    text = raw.decode("utf-8", errors="replace").strip()

    # 如果已经是 Clash/Mihomo YAML
    if (
        "proxies:" in text
        or "proxy-groups:" in text
        or "mixed-port:" in text
        or "rules:" in text
    ):
        return text

    # 否则尝试 Base64
    try:
        padded = text + "=" * (-len(text) % 4)

        decoded = base64.b64decode(
            padded,
            validate=False,
        )

        decoded_text = decoded.decode(
            "utf-8",
            errors="replace",
        ).strip()

        if (
            "proxies:" in decoded_text
            or "proxy-groups:" in decoded_text
            or "mixed-port:" in decoded_text
            or "rules:" in decoded_text
        ):
            return decoded_text

    except Exception:
        pass

    raise RuntimeError(
        "无法识别机场订阅格式。"
        "当前脚本需要机场返回 Clash/Mihomo YAML "
        "或 Base64 编码的 Clash/Mihomo YAML。"
    )


# ============================================================
# 3. 动态家宽地区
# ============================================================

REGIONS = [
    (
        "🇭🇰 香港动态家宽",
        r"(?i)(🇭🇰|香港).*动态.*家宽|(?i)(🇭🇰|香港).*家宽.*动态",
    ),
    (
        "🇹🇼 台湾动态家宽",
        r"(?i)(🇹🇼|台湾).*动态.*家宽|(?i)(🇹🇼|台湾).*家宽.*动态",
    ),
    (
        "🇯🇵 日本动态家宽",
        r"(?i)(🇯🇵|日本).*动态.*家宽|(?i)(🇯🇵|日本).*家宽.*动态",
    ),
    (
        "🇸🇬 新加坡动态家宽",
        r"(?i)(🇸🇬|新加坡|狮城).*动态.*家宽|(?i)(🇸🇬|新加坡|狮城).*家宽.*动态",
    ),
    (
        "🇰🇷 韩国动态家宽",
        r"(?i)(🇰🇷|韩国).*动态.*家宽|(?i)(🇰🇷|韩国).*家宽.*动态",
    ),
    (
        "🇺🇸 美国动态家宽",
        r"(?i)(🇺🇸|美国|USA|US).*动态.*家宽|(?i)(🇺🇸|美国|USA|US).*家宽.*动态",
    ),
    (
        "🇨🇦 加拿大动态家宽",
        r"(?i)(🇨🇦|加拿大|Canada).*动态.*家宽|(?i)(🇨🇦|加拿大|Canada).*家宽.*动态",
    ),
    (
        "🇬🇧 英国动态家宽",
        r"(?i)(🇬🇧|英国|UK|United Kingdom).*动态.*家宽|(?i)(🇬🇧|英国|UK|United Kingdom).*家宽.*动态",
    ),
    (
        "🇩🇪 德国动态家宽",
        r"(?i)(🇩🇪|德国|Germany).*动态.*家宽|(?i)(🇩🇪|德国|Germany).*家宽.*动态",
    ),
    (
        "🇫🇷 法国动态家宽",
        r"(?i)(🇫🇷|法国|France).*动态.*家宽|(?i)(🇫🇷|法国|France).*家宽.*动态",
    ),
    (
        "🇳🇱 荷兰动态家宽",
        r"(?i)(🇳🇱|荷兰|Netherlands).*动态.*家宽|(?i)(🇳🇱|荷兰|Netherlands).*家宽.*动态",
    ),
    (
        "🇦🇺 澳大利亚动态家宽",
        r"(?i)(🇦🇺|澳大利亚|澳洲|Australia).*动态.*家宽|(?i)(🇦🇺|澳大利亚|澳洲|Australia).*家宽.*动态",
    ),
]


# ============================================================
# 4. 排除关键词
# ============================================================

COMMON_EXCLUDE = r"(?i)流量|到期|超时"


# ============================================================
# 5. 其他动态家宽
# ============================================================

OTHER_REGION_EXCLUDE = (
    r"(?i)"
    r"(🇭🇰|香港|"
    r"🇹🇼|台湾|"
    r"🇯🇵|日本|"
    r"🇸🇬|新加坡|狮城|"
    r"🇰🇷|韩国|"
    r"🇺🇸|美国|USA|US|"
    r"🇨🇦|加拿大|Canada|"
    r"🇬🇧|英国|UK|United Kingdom|"
    r"🇩🇪|德国|Germany|"
    r"🇫🇷|法国|France|"
    r"🇳🇱|荷兰|Netherlands|"
    r"🇦🇺|澳大利亚|澳洲|Australia)"
)


# ============================================================
# 6. Google / AI 规则
#
# 故意没有把整个 google.com / googleapis.com 全部接管，
# 避免普通 Google 流量全部走家宽。
# ============================================================

AI_RULES = [
    "DOMAIN-SUFFIX,gemini.google.com,Google & AI",
    "DOMAIN-SUFFIX,generativelanguage.googleapis.com,Google & AI",
    "DOMAIN-SUFFIX,ai.google.dev,Google & AI",
    "DOMAIN-SUFFIX,aistudio.google.com,Google & AI",
]


# ============================================================
# 7. 创建策略组
# ============================================================

def build_proxy_groups(config: dict):
    proxy_groups = config.setdefault("proxy-groups", [])

    if not isinstance(proxy_groups, list):
        raise RuntimeError("机场配置中的 proxy-groups 不是列表。")

    existing_names = {
        group.get("name")
        for group in proxy_groups
        if isinstance(group, dict)
    }

    new_groups = []

    # --------------------------------------------------------
    # 各地区动态家宽
    # --------------------------------------------------------

    for name, regex in REGIONS:

        if name in existing_names:
            continu
