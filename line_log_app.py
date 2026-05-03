import streamlit as st
import pandas as pd
import re
import hashlib
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="LINEログ整理アプリ", layout="wide")


def _inject_css():
    st.markdown("""
    <style>
    /* ── ページ背景 ── */
    .stApp { background: #f1f5f9; }
    .main .block-container {
        padding-top: 24px !important;
        padding-bottom: 40px !important;
    }

    /* ── ファイルアップローダー ── */
    [data-testid="stFileUploader"] {
        background: rgba(13,148,136,0.04);
        border: 2px dashed #99f6e4;
        border-radius: 10px;
        padding: 8px;
        transition: border-color 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #0d9488;
    }

    /* ── 削除ボタン（primary） ── */
    div.stButton > button[kind="primary"] {
        background: #ef4444 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        box-shadow: 0 2px 8px rgba(239,68,68,0.25) !important;
        transition: all 0.2s !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #dc2626 !important;
        box-shadow: 0 4px 12px rgba(239,68,68,0.35) !important;
    }

    /* ── ダウンロードボタン ── */
    div.stDownloadButton > button {
        background: linear-gradient(135deg, #0f766e, #0d9488) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 11px 24px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        box-shadow: 0 3px 12px rgba(13,148,136,0.30) !important;
        transition: all 0.2s !important;
        width: auto !important;
    }
    div.stDownloadButton > button:hover {
        box-shadow: 0 5px 16px rgba(13,148,136,0.40) !important;
    }

    /* ── セレクトボックス ── */
    [data-testid="stSelectbox"] > div > div {
        border-color: #cbd5e1 !important;
        border-radius: 8px !important;
        background: white !important;
    }
    [data-testid="stSelectbox"] > div > div:focus-within {
        border-color: #0d9488 !important;
        box-shadow: 0 0 0 3px rgba(13,148,136,0.15) !important;
    }

    /* ── データエディター ── */
    [data-testid="stDataEditor"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
    }

    /* ── メトリクスカード ── */
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }

    /* ── st.success / st.warning の角丸 ── */
    [data-testid="stNotification"] {
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)


CATEGORY_RULES = {
    "事故": ["事故", "接触", "ぶつけ", "破損", "クレーム", "巻き込み", "転倒", "怪我", "けが"],
    "車両": ["車両", "トラック", "点検", "修理", "故障", "オイル", "タイヤ", "バッテリー", "ゲート", "スリップサイン"],
    "アルコール": ["アルコール", "酒気", "飲酒", "検知", "点呼"],
    "求人・面接": ["求人", "応募", "面接", "採用", "履歴書", "在籍確認"],
    "派遣ドライバー": ["派遣", "応援", "代走"],
    "始末書・顛末書": ["始末書", "顛末書", "報告書", "反省文"],
    "進捗": ["進捗", "確認", "完了", "未完了", "対応中"],
    "勤怠": ["欠勤", "遅刻", "早退", "休み", "有休", "体調不良"],
}

PROGRESS_OPTIONS = [
    "未対応",
    "対応中",
    "確認中",
    "完了",
    "保留",
    "不要",
]

BASE_COLUMNS = [
    "ログID",
    "日付",
    "時間",
    "発言者",
    "内容",
    "分類",
    "進捗状況",
    "備考",
]


def classify_message(text):
    text = str(text)
    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in text:
                return category
    return "その他"


def decode_text(raw):
    for enc in ["utf-8-sig", "utf-8", "cp932", "shift_jis"]:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def parse_line_log(text):
    rows = []
    current_date_text = ""
    current_date_value = None

    date_pattern = re.compile(r"^(\d{4}/\d{1,2}/\d{1,2})")
    message_tab_pattern = re.compile(r"^(\d{1,2}:\d{2})\t([^\t]+)\t(.*)$")
    message_space_pattern = re.compile(r"^(\d{1,2}:\d{2})\s+(.+?)\s+(.+)$")

    last_index = None

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        date_match = date_pattern.match(line)
        if date_match:
            current_date_text = line
            current_date_value = date_match.group(1)
            continue

        match = message_tab_pattern.match(line)

        if not match:
            match = message_space_pattern.match(line)

        if match:
            time = match.group(1)
            speaker = match.group(2)
            message = match.group(3)

            rows.append({
                "日付": current_date_text,
                "日付変換用": current_date_value,
                "時間": time,
                "発言者": speaker,
                "内容": message,
                "分類": classify_message(message),
            })
            last_index = len(rows) - 1
        else:
            if last_index is not None:
                rows[last_index]["内容"] += "\n" + line
                rows[last_index]["分類"] = classify_message(rows[last_index]["内容"])

    return pd.DataFrame(rows)


def filter_recent_3_months_and_remove_duplicates(df):
    if df.empty:
        return df, 0, 0, None, None

    original_count = len(df)

    df["日付変換用"] = pd.to_datetime(df["日付変換用"], errors="coerce")
    df = df.dropna(subset=["日付変換用"]).copy()

    if df.empty:
        return df, original_count, 0, None, None

    latest_date = df["日付変換用"].max().normalize()
    start_date = latest_date - pd.DateOffset(months=3)

    df = df[
        (df["日付変換用"] >= start_date) &
        (df["日付変換用"] <= latest_date)
    ].copy()

    after_date_filter_count = len(df)
    date_filtered_removed_count = original_count - after_date_filter_count

    df = df.drop_duplicates(
        subset=["日付", "時間", "発言者", "内容"],
        keep="first"
    ).copy()

    duplicate_removed_count = after_date_filter_count - len(df)

    df["時間ソート用"] = pd.to_datetime(
        df["時間"],
        format="%H:%M",
        errors="coerce"
    )

    df = df.sort_values(
        by=["日付変換用", "時間ソート用"],
        ascending=[False, False]
    ).copy()

    df = df.drop(columns=["日付変換用", "時間ソート用"])
    df = df.reset_index(drop=True)

    df.insert(0, "ログID", range(1, len(df) + 1))

    return df, date_filtered_removed_count, duplicate_removed_count, start_date, latest_date


def prepare_work_columns(df):
    df = df.copy()

    if "進捗状況" not in df.columns:
        df["進捗状況"] = "未対応"

    if "備考" not in df.columns:
        df["備考"] = ""

    return df[BASE_COLUMNS]


def merge_edits_to_current(edited_df):
    current_df = st.session_state.current_df.copy()

    if edited_df is not None and not edited_df.empty:
        for _, row in edited_df.iterrows():
            log_id = row["ログID"]
            mask = current_df["ログID"] == log_id

            current_df.loc[mask, "進捗状況"] = row["進捗状況"]
            current_df.loc[mask, "備考"] = row["備考"]

    st.session_state.current_df = current_df


def to_excel(main_df, deleted_df):
    output = BytesIO()

    export_main = main_df.drop(columns=["ログID"], errors="ignore").copy()
    export_deleted = deleted_df.drop(columns=["ログID"], errors="ignore").copy()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_main.to_excel(writer, index=False, sheet_name="整理結果")
        export_deleted.to_excel(writer, index=False, sheet_name="削除結果一覧")

    output.seek(0)
    return output


def render_header(filename=None, start_date=None, latest_date=None):
    period_html = ""
    if filename and start_date is not None and latest_date is not None:
        period_html = f"""
        <div style="text-align:right;">
          <div style="color:white;font-size:13px;font-weight:600;">{filename}</div>
          <div style="color:#ccfbf1;font-size:11px;margin-top:2px;">
            対象期間: {start_date.strftime('%Y/%m/%d')} 〜 {latest_date.strftime('%Y/%m/%d')}
          </div>
        </div>"""
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0f766e,#0d9488);
                padding:20px 28px;border-radius:12px;
                display:flex;align-items:center;justify-content:space-between;
                margin-bottom:20px;box-shadow:0 4px 16px rgba(13,148,136,0.25);">
      <div>
        <div style="color:white;font-size:20px;font-weight:700;letter-spacing:0.02em;">
          LINE ログ整理アプリ
        </div>
        <div style="color:#99f6e4;font-size:12px;margin-top:3px;">
          物流チーム用 · トーク履歴管理ツール
        </div>
      </div>
      {period_html}
    </div>
    """, unsafe_allow_html=True)


def render_kpi_cards(current_df, deleted_df):
    total = len(current_df)
    accident = int(current_df["分類"].eq("事故").sum()) if not current_df.empty else 0
    vehicle = int(current_df["分類"].eq("車両").sum()) if not current_df.empty else 0
    unhandled = int(current_df["進捗状況"].eq("未対応").sum()) if not current_df.empty else 0

    def card(label, value, color, sub):
        return f"""
        <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:16px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.05);">
          <div style="width:8px;height:8px;border-radius:50%;background:{color};margin-bottom:8px;"></div>
          <div style="font-size:11px;color:#94a3b8;font-weight:600;letter-spacing:0.06em;
                      text-transform:uppercase;margin-bottom:6px;">{label}</div>
          <div style="font-size:28px;font-weight:800;color:{color};line-height:1;">{value}</div>
          <div style="font-size:10px;color:#94a3b8;margin-top:4px;">{sub}</div>
        </div>"""

    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(card("総件数", total, "#0d9488", "直近3か月"), unsafe_allow_html=True)
    col2.markdown(card("事故", accident, "#ef4444", "要対応"), unsafe_allow_html=True)
    col3.markdown(card("車両関連", vehicle, "#f59e0b", "点検・修理含む"), unsafe_allow_html=True)
    col4.markdown(card("未対応", unhandled, "#6366f1", "要確認"), unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)


def render_info_banner(date_removed, duplicate_removed, start_date, latest_date):
    if start_date is None or latest_date is None:
        return
    st.markdown(f"""
    <div style="background:#f0fdfa;border:1px solid #99f6e4;border-radius:8px;
                padding:10px 16px;font-size:12px;color:#0f766e;
                display:flex;align-items:center;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
      <span style="width:6px;height:6px;border-radius:50%;background:#0d9488;
                   flex-shrink:0;display:inline-block;"></span>
      抽出基準日: <strong>{latest_date.strftime('%Y/%m/%d')}</strong> &nbsp;|&nbsp;
      対象期間: <strong>{start_date.strftime('%Y/%m/%d')} 〜 {latest_date.strftime('%Y/%m/%d')}</strong>
      &nbsp;|&nbsp; 期間外除外: <strong>{date_removed}件</strong>
      &nbsp;|&nbsp; 重複削除: <strong>{duplicate_removed}件</strong>
    </div>
    """, unsafe_allow_html=True)


def section_title(text, count=None):
    count_html = (
        f'<span style="font-weight:400;font-size:12px;color:#94a3b8;'
        f'text-transform:none;letter-spacing:0;margin-left:6px;">{count}件</span>'
        if count is not None else ""
    )
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;margin:20px 0 12px;">
      <span style="font-size:13px;font-weight:700;color:#475569;
                   letter-spacing:0.08em;text-transform:uppercase;">{text}</span>
      {count_html}
      <div style="flex:1;height:1px;background:#e2e8f0;"></div>
    </div>
    """, unsafe_allow_html=True)


_inject_css()
render_header()

uploaded_file = st.file_uploader(
    "LINEログのテキストファイルをアップロードしてください",
    type=["txt"]
)

if uploaded_file is not None:
    raw = uploaded_file.getvalue()
    file_hash = hashlib.md5(raw).hexdigest()
    text = decode_text(raw)

    if st.session_state.get("file_hash") != file_hash:
        parsed_df = parse_line_log(text)

        if parsed_df.empty:
            st.session_state.file_hash = file_hash
            st.session_state.current_df = pd.DataFrame(columns=BASE_COLUMNS)
            st.session_state.deleted_df = pd.DataFrame(columns=["削除日時"] + BASE_COLUMNS)
            st.session_state.date_removed_count = 0
            st.session_state.duplicate_removed_count = 0
            st.session_state.start_date = None
            st.session_state.latest_date = None
            st.session_state.parse_failed = True
        else:
            processed_df, date_removed_count, duplicate_removed_count, start_date, latest_date = (
                filter_recent_3_months_and_remove_duplicates(parsed_df)
            )

            processed_df = prepare_work_columns(processed_df)

            st.session_state.file_hash = file_hash
            st.session_state.current_df = processed_df
            st.session_state.deleted_df = pd.DataFrame(columns=["削除日時"] + BASE_COLUMNS)
            st.session_state.date_removed_count = date_removed_count
            st.session_state.duplicate_removed_count = duplicate_removed_count
            st.session_state.start_date = start_date
            st.session_state.latest_date = latest_date
            st.session_state.parse_failed = False

    st.success("ファイルを読み込みました。")
    st.write(f"ファイル名：{uploaded_file.name}")

    if st.session_state.get("parse_failed"):
        st.warning("ログを表に変換できませんでした。LINEのトーク履歴形式を確認してください。")
        st.text_area("読み込んだ内容の確認", text[:3000], height=300)

    else:
        latest_date = st.session_state.latest_date
        start_date = st.session_state.start_date

        if latest_date is not None:
            st.info(f"抽出基準日：{latest_date.strftime('%Y/%m/%d')}")
            st.info(f"対象期間：{start_date.strftime('%Y/%m/%d')} ～ {latest_date.strftime('%Y/%m/%d')}")

        st.info(f"対象期間外のデータを {st.session_state.date_removed_count} 件除外しました。")
        st.info(f"重複データを {st.session_state.duplicate_removed_count} 件削除しました。")

        current_df = st.session_state.current_df.copy()
        deleted_df = st.session_state.deleted_df.copy()

        st.write(f"現在の整理結果：{len(current_df)} 件")
        st.write(f"削除結果一覧：{len(deleted_df)} 件")

        if current_df.empty:
            st.warning("整理結果に表示するデータがありません。")

        else:
            st.subheader("整理結果")

            categories = ["すべて"] + sorted(current_df["分類"].unique().tolist())
            selected_category = st.selectbox("分類で絞り込み", categories)

            if selected_category != "すべて":
                display_df = current_df[current_df["分類"] == selected_category].copy()
            else:
                display_df = current_df.copy()

            display_df = display_df.reset_index(drop=True)
            display_df.insert(0, "削除", False)

            st.write("削除したいログは左端の「削除」にチェックを入れて、下の削除ボタンを押してください。")
            st.write("進捗状況はプルダウンで選択できます。備考欄には自由に入力できます。")

            editor_key = f"editor_{file_hash}_{selected_category}_{len(current_df)}"

            edited_df = st.data_editor(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=520,
                key=editor_key,
                column_config={
                    "ログID": None,
                    "削除": st.column_config.CheckboxColumn(
                        "削除",
                        help="削除したいログにチェックを入れてください。",
                        default=False,
                    ),
                    "進捗状況": st.column_config.SelectboxColumn(
                        "進捗状況",
                        help="対応状況を選択してください。",
                        options=PROGRESS_OPTIONS,
                        required=True,
                    ),
                    "備考": st.column_config.TextColumn(
                        "備考",
                        help="補足事項や対応メモを入力してください。",
                    ),
                    "内容": st.column_config.TextColumn(
                        "内容",
                        width="large",
                    ),
                },
                disabled=[
                    "日付",
                    "時間",
                    "発言者",
                    "内容",
                    "分類",
                ],
            )

            merge_edits_to_current(edited_df)

            checked_count = int(edited_df["削除"].fillna(False).sum())

            if checked_count > 0:
                st.warning(f"{checked_count} 件が削除対象として選択されています。")

            if st.button("チェックしたログを削除して、削除結果一覧へ移動する", type="primary"):
                delete_ids = edited_df.loc[
                    edited_df["削除"].fillna(False) == True,
                    "ログID"
                ].tolist()

                if len(delete_ids) == 0:
                    st.warning("削除対象が選択されていません。")
                else:
                    current_df = st.session_state.current_df.copy()

                    rows_to_delete = current_df[current_df["ログID"].isin(delete_ids)].copy()
                    rows_to_delete.insert(
                        0,
                        "削除日時",
                        datetime.now().strftime("%Y/%m/%d %H:%M")
                    )

                    st.session_state.deleted_df = pd.concat(
                        [st.session_state.deleted_df, rows_to_delete],
                        ignore_index=True
                    )

                    st.session_state.current_df = current_df[
                        ~current_df["ログID"].isin(delete_ids)
                    ].copy().reset_index(drop=True)

                    st.success(f"{len(delete_ids)} 件を整理結果から削除し、削除結果一覧へ移動しました。")
                    st.rerun()

        st.subheader("分類別件数")

        if st.session_state.current_df.empty:
            st.warning("分類別件数を表示するデータがありません。")
        else:
            count_df = st.session_state.current_df["分類"].value_counts().reset_index()
            count_df.columns = ["分類", "件数"]
            st.dataframe(count_df, use_container_width=True, hide_index=True)

        st.subheader("削除結果一覧")

        if st.session_state.deleted_df.empty:
            st.write("削除されたログはまだありません。")
        else:
            deleted_display = st.session_state.deleted_df.drop(columns=["ログID"], errors="ignore")
            st.dataframe(deleted_display, use_container_width=True, hide_index=True)

        excel_data = to_excel(st.session_state.current_df, st.session_state.deleted_df)

        st.download_button(
            label="整理結果と削除結果一覧をExcelでダウンロード",
            data=excel_data,
            file_name="LINEログ整理結果_削除結果一覧付き.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
