import os
import base64
import urllib.request
from pathlib import Path

import yaml

SUB_URL = os.environ.get("XUESHAN_SUB_URL")

if not SUB_URL:
    raise RuntimeError("没有找到 XUESHAN_SUB_URL")


def get_subscription(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "clash.meta"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
            print("订阅 HTTP 状态:", getattr(r, "status", "?"), "长度:", len(data))
    except Exception as e:
        raise RuntimeError(f"拉取订阅失败: {e}") from e
    text = data.decode("utf-8", errors="replace").strip()
    if "proxies:" in text:
        return text
    try:
        decoded = base64.b64decode(text + "=" * (-len(text) % 4)).decode("utf-8", errors="replace").strip()
        if "proxies:" in decoded:
            return decoded
    except Exception:
        pass
    raise RuntimeError("机场订阅不是 Clash/Mihomo YAML 或 Base64 YAML")


REGIONS = [
    ("🇭🇰 香港动态家宽", r"(?i)(🇭🇰|香港).*(动态|家宽)"),
    ("🇹🇼 台湾动态家宽", r"(?i)(🇹🇼|台湾).*(动态|家宽)"),
    ("🇯🇵 日本动态家宽", r"(?i)(🇯🇵|日本).*(动态|家宽)"),
    ("🇸🇬 新加坡动态家宽", r"(?i)(🇸🇬|新加坡|狮城).*(动态|家宽)"),
    ("🇰🇷 韩国动态家宽", r"(?i)(🇰🇷|韩国).*(动态|家宽)"),
    ("🇺🇸 美国动态家宽", r"(?i)(🇺🇸|美国|USA|\bUS\b).*(动态|家宽)"),
    ("🇨🇦 加拿大动态家宽", r"(?i)(🇨🇦|加拿大|Canada).*(动态|家宽)"),
    ("🇬🇧 英国动态家宽", r"(?i)(🇬🇧|英国|UK|United Kingdom).*(动态|家宽)"),
    ("🇩🇪 德国动态家宽", r"(?i)(🇩🇪|德国|Germany).*(动态|家宽)"),
    ("🇫🇷 法国动态家宽", r"(?i)(🇫🇷|法国|France).*(动态|家宽)"),
    ("🇳🇱 荷兰动态家宽", r"(?i)(🇳🇱|荷兰|Netherlands).*(动态|家宽)"),
    ("🇦🇺 澳大利亚动态家宽", r"(?i)(🇦🇺|澳大利亚|澳洲|Australia).*(动态|家宽)"),
]

AI_RULES = [
    "DOMAIN-SUFFIX,gemini.google.com,Google & AI",
    "DOMAIN-SUFFIX,generativelanguage.googleapis.com,Google & AI",
    "DOMAIN-SUFFIX,ai.google.dev,Google & AI",
    "DOMAIN-SUFFIX,aistudio.google.com,Google & AI",
]


def main() -> None:
    print("正在获取机场订阅...")
    config = yaml.safe_load(get_subscription(SUB_URL))
    if not isinstance(config, dict):
        raise RuntimeError("订阅解析失败")
    if not isinstance(config.get("proxies"), list):
        raise RuntimeError("订阅中没有 proxies")
    print("原节点数量:", len(config["proxies"]))
    groups = config.setdefault("proxy-groups", [])
    if not isinstance(groups, list):
        groups = []
    existing = {g.get("name") for g in groups if isinstance(g, dict)}
    new_groups = []
    for name, regex in REGIONS:
        if name not in existing:
            new_groups.append({
                "name": name,
                "type": "select",
                "include-all": True,
                "filter": regex,
                "exclude-filter": r"(?i)流量|到期|超时|官网|剩余",
            })
    other = "🌍 其他动态家宽"
    if other not in existing:
        exclude = r"(?i)🇭🇰|香港|🇹🇼|台湾|🇯🇵|日本|🇸🇬|新加坡|狮城|🇰🇷|韩国|🇺🇸|美国|USA|\bUS\b|🇨🇦|加拿大|Canada|🇬🇧|英国|UK|United Kingdom|🇩🇪|德国|Germany|🇫🇷|法国|France|🇳🇱|荷兰|Netherlands|🇦🇺|澳大利亚|澳洲|Australia|流量|到期|超时|官网|剩余"
        new_groups.append({
            "name": other,
            "type": "select",
            "include-all": True,
            "filter": r"(?i)动态|家宽",
            "exclude-filter": exclude,
        })
    if "Google & AI" not in existing:
        new_groups.append({
            "name": "Google & AI",
            "type": "select",
            "proxies": [name for name, _ in REGIONS] + [other],
        })
    config["proxy-groups"] = new_groups + groups
    config["rules"] = AI_RULES + list(config.get("rules") or [])
    names = {g.get("name") for g in config["proxy-groups"] if isinstance(g, dict)}
    if "Google & AI" not in names:
        raise RuntimeError("Google & AI 创建失败")
    Path("generated-config.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False, width=4096),
        encoding="utf-8",
    )
    print("生成成功")
    print("最终节点数量:", len(config["proxies"]))
    print("策略组数量:", len(config["proxy-groups"]))


if __name__ == "__main__":
    main()
