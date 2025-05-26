import streamlit as st
import json
from deepdiff import DeepDiff
from json_diff_viewer_v2_05261123 import format_diff, extract_time

st.set_page_config(page_title="JSON 差異比對工具", layout="wide")

st.title("🧪 JSON 差異比對工具")

uploaded_file1 = st.file_uploader("請上傳第一個檔案（不限副檔名，內容需為 JSON）", key="file1")
uploaded_file2 = st.file_uploader("請上傳第二個檔案（不限副檔名，內容需為 JSON）", key="file2")


def try_load_json(file, label):
    try:
        return json.load(file), None
    except json.JSONDecodeError:
        return None, f"❌ {label} 的內容不是合法 JSON 格式"
    except Exception as e:
        return None, f"❌ {label} 載入失敗：{e}"

if uploaded_file1 and uploaded_file2:
    data1, error1 = try_load_json(uploaded_file1, "第一個檔案")
    data2, error2 = try_load_json(uploaded_file2, "第二個檔案")

    if error1:
        st.error(error1)
    if error2:
        st.error(error2)

    if data1 and data2:
        exclude_paths = ["root['Items'][*]['modified']", "root['Items'][*]['created']"]
        diff = DeepDiff(data1, data2, verbose_level=2, exclude_paths=exclude_paths)

        time1 = extract_time(data1)
        time2 = extract_time(data2)
        subtitle = f"📅 比較時間：檔案1 = {time1}，檔案2 = {time2}"

        st.subheader(subtitle)
        st.code(format_diff(diff, data1), language="text")
