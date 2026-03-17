import streamlit as st
import sqlite3
import pandas as pd
import os
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import urllib.request

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

    # --- 主畫面：新聞展示與趨勢分析 ---
    st.subheader(f"📑 篩選結果：共 {len(filtered_df)} 篇")
    
    if len(filtered_df) == 0:
        st.info("找不到符合條件的新聞，請嘗試調整左側的篩選條件。")
        return
        
    tab1, tab2 = st.tabs(["📑 新聞列表", "📈 趨勢分析"])
    
    with tab1:
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

    with tab2:
        st.markdown("### 📊 數據統計與熱門關鍵字")
        st.markdown("以下圖表基於目前左側欄篩選出的新聞數量進行統計。")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("#### 📌 依分類統計")
            category_counts = filtered_df['category'].value_counts()
            st.bar_chart(category_counts)
            
        with col_chart2:
            st.markdown("#### 📰 依來源統計")
            source_counts = filtered_df['source'].value_counts()
            st.bar_chart(source_counts)
            
        st.markdown("---")
        st.markdown("#### ☁️ 摘要關鍵字文字雲")
        
        # 生成文字雲
        text_content = " ".join(filtered_df['summary'].dropna().tolist())
        
        if text_content.strip():
            # 使用 jieba 進行中文斷詞
            words = jieba.cut(text_content)
            # 過濾常見無意義停用詞
            stop_words = {"的", "在", "是", "與", "及", "和", "了", "有", "為", "以", "等", "也", "將", "對", "就", "未分類", "延伸閱讀", "趨勢摘要", "預防", "早篩", "治療", "無相關資訊"}
            filtered_words = [str(w) for w in words if str(w) not in stop_words and len(str(w)) > 1]
            processed_text = " ".join(filtered_words)
            
            # 使用公版中文字型避免亂碼，如果雲端環境沒有會自動下載開源字體
            font_path = "NotoSansTC-Regular.otf"
            if not os.path.exists(font_path) and os.name != 'nt':
                try:
                    urllib.request.urlretrieve("https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf", font_path)
                except:
                    font_path = None
                    
            if os.name == 'nt' and (font_path is None or not os.path.exists(font_path)):
                 # Windows 也可以直接使用內建字體
                 font_path = "C:/Windows/Fonts/msjh.ttc"
            
            try:
                wordcloud = WordCloud(
                    width=800, 
                    height=400, 
                    background_color='white',
                    font_path=font_path,
                    colormap='ocean'
                ).generate(processed_text)
                
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"目前環境無法生成文字雲：{e}")
        else:
            st.info("目前沒有足夠的摘要文字以生成文字雲。")

if __name__ == "__main__":
    main()
