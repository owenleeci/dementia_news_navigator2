import streamlit as st
import sqlite3
import pandas as pd
import os

# 網頁設定：將標題與圖示設定好，並改為寬螢幕模式以呈現更多資訊
st.set_page_config(
    page_title="失智症新聞自動導航員",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 使用自訂的 CSS 來美化介面 (加入一些微光質感和排版調整)
st.markdown("""
<style>
    /* 調整主標題顏色 */
    h1 {
        color: #2e6c80;
        text-align: center;
        margin-bottom: 30px;
    }
    /* 為每個新聞卡片加上邊框和陰影 */
    div[data-testid="stExpander"] {
        background-color: #f9f9fa;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    /* 調整內文段落距 */
    p {
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# 讀取 SQLite 資料庫的功能
@st.cache_data(ttl=3600) # 緩存資料 1 小時，避免頻繁讀取資料庫
def load_data():
    db_path = "output/dementia_news.db"
    if not os.path.exists(db_path):
        return pd.DataFrame()
        
    try:
        conn = sqlite3.connect(db_path)
        # 用 Pandas 讀取整張表
        query = "SELECT * FROM news ORDER BY published_at DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"無法讀取資料庫: {e}")
        return pd.DataFrame()

# 網頁主程式
def main():
    # 頂部標題
    st.title("🧠 失智症新聞自動導航員")
    st.markdown("每日為您精選、AI 總結各大醫學期刊與新聞網站的失智症重點資訊。")
    st.divider()

    # 讀取資料
    df = load_data()
    
    if df.empty:
        st.warning("目前資料庫中尚無新聞。請先執行爬蟲與 AI 處理管線 (main_pipeline.py)。")
        return

    # --- 側邊欄：進階篩選功能 ---
    with st.sidebar:
        st.header("🔍 資訊導航")
        
        # 1. 關鍵字搜尋
        search_term = st.text_input("輸入關鍵字搜尋", "")
        
        # 2. 分類篩選
        categories = ["全部"] + sorted(df['category'].dropna().unique().tolist())
        selected_category = st.selectbox("依分類篩選", categories)
        
        # 3. 來源篩選
        sources = ["全部"] + sorted(df['source'].dropna().unique().tolist())
        selected_source = st.selectbox("依來源篩選", sources)
        
        st.markdown("---")
        st.metric(label="目前資料庫新聞總數", value=len(df))
        st.caption("由 Gemini AI 驅動分類與摘要")

    # --- 資料過濾 ---
    filtered_df = df.copy()
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['title'].str.contains(search_term, case=False, na=False) |
            filtered_df['summary'].str.contains(search_term, case=False, na=False)
        ]
        
    if selected_category != "全部":
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
        
    if selected_source != "全部":
        filtered_df = filtered_df[filtered_df['source'] == selected_source]

    # --- 主畫面：新聞展示 ---
    st.subheader(f"📑 篩選結果：共 {len(filtered_df)} 篇")
    
    if len(filtered_df) == 0:
        st.info("找不到符合條件的新聞，請嘗試調整左側的篩選條件。")
    
    # 網格狀排列，每排兩欄
    col1, col2 = st.columns(2)
    
    # 將過濾後的資料轉為字典清單方便迴圈
    records = filtered_df.to_dict('records')
    
    for i, row in enumerate(records):
        # 交替放在左右兩欄
        col = col1 if i % 2 == 0 else col2
        
        with col:
            # 使用 Expander 來作為折疊式的新聞卡片
            # 標題加上來源和分類的標籤作為提示
            expander_title = f"{row['title']} | 🏷️ {row['category']} | 📰 {row['source']}"
            
            with st.expander(expander_title):
                st.caption(f"發布時間: {row['published_at']}")
                
                # 判斷 AI 摘要是否為空
                if pd.isna(row['summary']) or row['summary'].strip() == "":
                    st.write("此篇新聞尚無 AI 摘要內容。")
                    st.write(row['original_text'])
                else:
                    # 直接渲染 Markdown 格式的摘要，這就是我們五段式 Prompt 發揮威力的地方
                    st.markdown(row['summary'])

if __name__ == "__main__":
    main()
