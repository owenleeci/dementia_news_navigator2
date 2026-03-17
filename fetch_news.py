import feedparser
import pandas as pd
from datetime import datetime
import os

# 目標：從 Google News RSS 抓取特定關鍵字的新聞

def fetch_google_news(keyword="失智症", max_items=5):
    """
    從 Google News 抓取指定關鍵字的新聞 RSS
    """
    print(f"正在抓取關鍵字: {keyword} 的新聞...")
    
    # 這是 Google News 特定的 RSS 網址結構
    # hl=zh-TW (語言: 繁體中文), gl=TW (地區: 台灣), ceid=TW:zh-Hant
    rss_url = f"https://news.google.com/rss/search?q={keyword}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    # 使用 feedparser 解析 RSS 網址
    feed = feedparser.parse(rss_url)
    
    # 儲存結果的列表
    news_list = []
    
    # 檢查是否成功抓到資料
    if feed.entries:
        print(f"✅ 成功找到新聞，共 {len(feed.entries)} 篇，預計處理前 {max_items} 篇。")
        
        # 迴圈讀取每一篇新聞 (限制抓取數量)
        for i, entry in enumerate(feed.entries[:max_items]):
            
            # 從 RSS 欄位中提取需要的資訊
            title = entry.title
            link = entry.link
            
            # 處理時間格式 (RSS 預設是 struct_time)
            # 有些 feed 格式可能沒有 published_parsed，需要加上 try-except 保護
            try:
                 pub_date = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d %H:%M:%S')
            except:
                 pub_date = entry.published # 如果解析失敗，直接存純文字
            
            # 將提取的資料存成字典
            news_data = {
                "Title": title,
                "Link": link,
                "Published Date": pub_date
            }
            news_list.append(news_data)
            
            print(f"- 標題 {i+1}: {title}")
    else:
        print("❌ 找不到任何新聞或連線失敗。")
        
    return news_list

if __name__ == "__main__":
    # 1. 測試抓取 5 篇新聞
    news_data = fetch_google_news(keyword="失智症", max_items=5)
    
    # 2. 如果有抓到資料，存成 Pandas DataFrame 並匯出成 CSV 方便查看
    if news_data:
        df = pd.DataFrame(news_data)
        
        # 建立 output 資料夾
        if not os.path.exists("output"):
            os.makedirs("output")
            
        csv_path = "output/dementia_news_test.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n✅ 測試成功！資料已儲存至 {csv_path}")
    
