#!/bin/zsh
# VOC Data Product — API Keys 配置脚本
# 用法：在终端执行 bash setup_api_keys.sh
# 会追加到 ~/.zshrc，新开终端后永久生效

set -e

ZSHRC="$HOME/.zshrc"
MARKER="# VOC Data Product API Keys"

echo ""
echo "=== VOC Data Product API Keys 配置 ==="
echo "写入位置：$ZSHRC"
echo ""

# 读取输入（不回显）
read_key() {
    local prompt="$1"
    local env_name="$2"
    local current
    current=$(grep "^export ${env_name}=" "$ZSHRC" 2>/dev/null | tail -1 | cut -d'"' -f2)
    if [ -n "$current" ]; then
        masked="${current:0:6}****"
        printf "%s (当前已配置: %s，回车跳过): " "$prompt" "$masked"
    else
        printf "%s (未配置，回车跳过): " "$prompt"
    fi
    local val
    read -rs val
    echo ""
    if [ -z "$val" ] && [ -n "$current" ]; then
        echo "$current"   # 保留现有值
    else
        echo "$val"
    fi
}

echo "请依次输入各 API Key（输入时不显示字符）："
echo ""

TIKHUB_KEY=$(read_key   "1. TikHub API Key   (TikTok/Reddit/YouTube 共用)" "TIKHUB_API_KEY")
KIMI_KEY=$(read_key     "2. Kimi API Key     (长文本洞察摘要)" "KIMI_API_KEY")
DEEPSEEK_KEY=$(read_key "3. DeepSeek API Key (推理/Action生成)" "DEEPSEEK_API_KEY")
APIFY_KEY=$(read_key    "4. Apify API Key    (Facebook Groups，可暂跳过)" "APIFY_API_KEY")

echo ""
echo "=== 配置预览 ==="

preview() {
    local name="$1"
    local val="$2"
    if [ -n "$val" ]; then
        local masked="${val:0:6}****"
        printf "  ✓ %-20s = %s\n" "$name" "$masked"
    else
        printf "  - %-20s (跳过)\n" "$name"
    fi
}

preview "TIKHUB_API_KEY"   "$TIKHUB_KEY"
preview "KIMI_API_KEY"     "$KIMI_KEY"
preview "DEEPSEEK_API_KEY" "$DEEPSEEK_KEY"
preview "APIFY_API_KEY"    "$APIFY_KEY"

echo ""
printf "确认写入 ~/.zshrc 并立即生效？[Y/n] "
read -r confirm
if [[ "$confirm" =~ ^[Nn]$ ]]; then
    echo "已取消。"
    exit 0
fi

# 删除旧的 VOC Keys 块（如果存在），避免重复
if grep -q "$MARKER" "$ZSHRC" 2>/dev/null; then
    # 删除从 marker 到下一个空行的内容
    python3 - <<PYEOF
import re
with open("$ZSHRC", "r") as f:
    content = f.read()
# 删除 marker 开始的整个块
cleaned = re.sub(r'\n$MARKER\n(?:export [^\n]+\n)*', '\n', content)
with open("$ZSHRC", "w") as f:
    f.write(cleaned)
PYEOF
fi

# 追加新的 Keys 块
{
    echo ""
    echo "$MARKER"
    [ -n "$TIKHUB_KEY"   ] && echo "export TIKHUB_API_KEY=\"$TIKHUB_KEY\""
    [ -n "$KIMI_KEY"     ] && echo "export KIMI_API_KEY=\"$KIMI_KEY\""
    [ -n "$DEEPSEEK_KEY" ] && echo "export DEEPSEEK_API_KEY=\"$DEEPSEEK_KEY\""
    [ -n "$APIFY_KEY"    ] && echo "export APIFY_API_KEY=\"$APIFY_KEY\""
} >> "$ZSHRC"

# 立即加载到当前 shell
[ -n "$TIKHUB_KEY"   ] && export TIKHUB_API_KEY="$TIKHUB_KEY"
[ -n "$KIMI_KEY"     ] && export KIMI_API_KEY="$KIMI_KEY"
[ -n "$DEEPSEEK_KEY" ] && export DEEPSEEK_API_KEY="$DEEPSEEK_KEY"
[ -n "$APIFY_KEY"    ] && export APIFY_API_KEY="$APIFY_KEY"

echo ""
echo "=== 写入完成 ==="

# 验证
echo ""
echo "当前会话验证："
for key in TIKHUB_API_KEY KIMI_API_KEY DEEPSEEK_API_KEY APIFY_API_KEY; do
    val="${!key}"
    if [ -n "$val" ]; then
        masked="${val:0:6}****"
        echo "  ✓ $key = $masked"
    else
        echo "  - $key (未配置)"
    fi
done

echo ""
echo "新开终端后自动生效。当前会话已立即生效。"
echo ""
echo "=== 下一步：验证 LLM API ==="
echo "  cd /Users/lute/Project/voc-data-product"
echo "  python3 tools/llm/client.py --check"
echo ""
echo "=== 第一次采集验证 ==="
echo "  python3 tools/social/reddit_collector.py --subreddit breastpumps --limit 15 --write-db"
echo ""
