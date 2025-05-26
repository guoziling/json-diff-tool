import sys
import json
from deepdiff import DeepDiff
from pathlib import Path
import webbrowser
from datetime import datetime

def pretty_json(data):
    return json.dumps(data, indent=4, ensure_ascii=False)

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_html(diff_text, output_path="result.html"):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <title>JSON 差異比較報告</title>
        <style>
            body {{ font-family: monospace; background: #f7f7f7; padding: 20px; }}
            pre {{ background: white; border: 1px solid #ccc; padding: 10px; white-space: pre-wrap; }}
            h2 {{ color: #333; }}
        </style>
    </head>
    <body>
        <h2>JSON 差異比較報告</h2>
        <pre>{diff_text}</pre>
    </body>
    </html>
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    webbrowser.open(output_path)

def extract_time(data):
    try:
        return data.get('Items', [{}])[0].get('modified', '未知')
    except Exception:
        return '未知'

def is_time_related(path_str):
    keywords = ["modified", "created", "timestamp", "time", "lastedModifiedAt"]
    return any(k.lower() in path_str.lower() for k in keywords)

def build_name_lookup(data):
    lookup = {}
    for i, item in enumerate(data.get("Items", [])):
        name = item.get("carParkFacilityNameTc")
        if not name:
            try:
                name = item["parkingInfoList"][0].get("carParkFacilityNameTc")
            except:
                name = None
        lookup[str(i)] = name if name else f"Items[{i}]"
    return lookup

def translate_path(path):
    translations = {
        "availableEVVancies": "（電動車剩餘位）",
        "availableEVVacancies": "（電動車剩餘位）",
        "availableVacancyList": "（各類車位明細）",
        "availableVacancy": "（可用車位數）",
        "availableCarParkSpace": "（總剩餘車位）",
        "type.DC": "（DC直流充電）",
        "type.AC": "（AC交流充電）"
    }
    translated = []
    for segment in path.split('.'):
        note = translations.get(segment, "")
        translated.append(segment + (note if note else ""))
    return '.'.join(translated)

def simplify_path(path, name_lookup):
    import re
    match = re.match(r"root\['Items'\]\[(\d+)\](.*)", path)
    if match:
        index = match.group(1)
        suffix = match.group(2)
        name = name_lookup.get(index, f"Items[{index}]")
        simplified = f"{name}{suffix}"
    else:
        simplified = path
    simplified = simplified.replace("['parkingInfoList']", "")
    simplified = simplified.replace("['", ".").replace("']", "")
    simplified = simplified.strip('.')
    return translate_path(simplified)

def format_diff(diff, data1):
    name_lookup = build_name_lookup(data1)
    lines = []

    if not diff:
        return "✅ 查詢無差異，兩份 JSON 結構一致（已排除時間欄位）"

    if "values_changed" in diff:
        lines.append("【值變動（values_changed）】")
        for path, change in diff["values_changed"].items():
            if is_time_related(path):
                continue
            simp = simplify_path(path, name_lookup)
            lines.append(f"🔸 {simp}")
            lines.append(f"　原值：{change['old_value']}")
            lines.append(f"　新值：{change['new_value']}")
            lines.append("")

    if "dictionary_item_added" in diff:
        lines.append("【新增鍵（dictionary_item_added）】")
        for path in diff["dictionary_item_added"]:
            if is_time_related(path):
                continue
            simp = simplify_path(path, name_lookup)
            lines.append(f"🟢 新增：{simp}")
        lines.append("")

    if "dictionary_item_removed" in diff:
        lines.append("【刪除鍵（dictionary_item_removed）】")
        for path in diff["dictionary_item_removed"]:
            if is_time_related(path):
                continue
            simp = simplify_path(path, name_lookup)
            lines.append(f"🔴 刪除：{simp}")
        lines.append("")

    if "type_changes" in diff:
        lines.append("【類型變動（type_changes）】")
        for path, change in diff["type_changes"].items():
            if is_time_related(path):
                continue
            simp = simplify_path(path, name_lookup)
            lines.append(f"🟡 {simp}")
            lines.append(f"　原類型：{change['old_type'].__name__}，原值：{change['old_value']}")
            lines.append(f"　新類型：{change['new_type'].__name__}，新值：{change['new_value']}")
            lines.append("")

    return "\n".join(lines)

def main():
    if len(sys.argv) != 3:
        print("用法: python json_diff_viewer_v2_05261123.py 檔案1.json 檔案2.json")
        sys.exit(1)

    file1_path = sys.argv[1]
    file2_path = sys.argv[2]

    try:
        data1 = load_json(file1_path)
        data2 = load_json(file2_path)
    except Exception as e:
        print(f"❌ 讀取 JSON 檔案失敗: {e}")
        sys.exit(1)

    exclude_paths = ["root['Items'][*]['modified']", "root['Items'][*]['created']"]
    diff = DeepDiff(data1, data2, verbose_level=2, exclude_paths=exclude_paths)

    time1 = extract_time(data1)
    time2 = extract_time(data2)
    subtitle = f"比較時間：檔案1 = {time1}，檔案2 = {time2}"

    diff_text = subtitle + "\n\n" + format_diff(diff, data1)
    save_html(diff_text)
    print("✅ 差異報告已產生，請查看 result.html")

if __name__ == "__main__":
    main()