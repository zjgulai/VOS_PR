"""
飞书多维表格 → 本地 config/biz_confirmation.json
用法：
  python3 tools/pmo/feishu_pull.py           # 拉取全部，打印摘要
  python3 tools/pmo/feishu_pull.py --check   # 只检查填写进度，不写文件

输出：config/biz_confirmation.json
结构：
{
  "pr": {
    "1.核心媒体与编辑": [{"媒体":"Forbes", "业务确认":"确认", ...}, ...],
    ...
  },
  "social": { ... }
}
"""
import subprocess, json, sys, time, argparse, os
from pathlib import Path

APP_ID     = os.environ.get('FEISHU_APP_ID', '')
APP_SECRET = os.environ.get('FEISHU_APP_SECRET', '')
BASE       = 'https://open.feishu.cn/open-apis'
PROJ       = Path(__file__).resolve().parents[2]
CONFIG     = PROJ / 'config' / 'feishu_bitable_config.json'
OUTPUT     = PROJ / 'config' / 'biz_confirmation.json'


def get_token():
    r = subprocess.run(
        f'curl -s -X POST "{BASE}/auth/v3/tenant_access_token/internal" '
        f'-H "Content-Type: application/json" '
        f'-d \'{{"app_id":"{APP_ID}","app_secret":"{APP_SECRET}"}}\' ',
        shell=True, capture_output=True, text=True, timeout=15)
    return json.loads(r.stdout)['tenant_access_token']


def api_get(path, token):
    cmd = f'curl -s "{BASE}{path}" -H "Authorization: Bearer {token}"'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
    return json.loads(r.stdout)


def pull_table(token, app_token, table_id):
    """拉取一个 table 的全部记录，返回 list[dict]"""
    records = []
    page_token = None
    while True:
        params = 'page_size=100'
        if page_token:
            params += f'&page_token={page_token}'
        d = api_get(f'/bitable/v1/apps/{app_token}/tables/{table_id}/records?{params}', token)
        items = d.get('data', {}).get('items') or []
        for item in items:
            records.append(item.get('fields', {}))
        if d.get('data', {}).get('has_more'):
            page_token = d['data'].get('page_token')
        else:
            break
    return records


def print_progress(team_name, table_name, records):
    """统计「业务确认」列的填写进度"""
    total = len(records)
    filled = sum(1 for r in records if r.get('业务确认') and str(r.get('业务确认')).strip())
    status = '✅' if filled == total and total > 0 else ('⏳' if filled > 0 else '❌')
    print(f'  {status} [{table_name}] {filled}/{total} 已确认')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='只检查进度，不写文件')
    args = parser.parse_args()

    if not CONFIG.exists():
        print(f'ERROR: {CONFIG} 不存在，请先运行推送脚本')
        sys.exit(1)

    bitable_config = json.loads(CONFIG.read_text(encoding='utf-8'))
    token = get_token()
    result = {}
    all_done = True

    for team_key in ('pr', 'social'):
        team = bitable_config[team_key]
        app_token = team['app_token']
        team_name = team['app_name']
        print(f'\n── {team_name} ──')
        result[team_key] = {}

        for table_name, meta in team['tables'].items():
            tid = meta['table_id']
            records = pull_table(token, app_token, tid)
            print_progress(team_name, table_name, records)
            result[team_key][table_name] = records

            unfilled = [r for r in records if not r.get('业务确认') or not str(r.get('业务确认')).strip()]
            if unfilled:
                all_done = False

    print(f'\n{"="*50}')
    if all_done:
        print('✅ 所有业务确认项已填写完毕，可进入下阶段开发')
    else:
        print('⏳ 仍有未填写项，等待业务团队确认')

    if not args.check:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'已写入 {OUTPUT.relative_to(PROJ)}')

    return result


if __name__ == '__main__':
    main()
