import sqlite3
import pandas as pd
from datetime import datetime
import time
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 匯入我們自己寫的模組
from fetch_news import fetch_google_news
from scraper_ntu import fetch_ntu_karenchen_news
from scraper_domestic_news import fetch_domestic_health_news
from ai_summarizer import generate_news_summary

# 如有需要，亦可匯入 Selenium 爬蟲，但執行成本較高，這裡以快速測試為主，先整合前三者
# from scraper_medical_journals_selenium import fetch_lancet_with_selenium, fetch_nejm_with_selenium, setup_driver

def init_db(db_name="dementia_news.db"):
    """
    初始化 SQLite 資料庫與建立資料表
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 建立 news 資料表
    # 採用你規劃的欄位結構：id, title, link, original_text, summary, category, published_at
    # summary 欄位將存放 AI 生成的完整五段式摘要
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            title TEXT,
            link TEXT UNIQUE,
            original_text TEXT,
            summary TEXT,
            category TEXT,
            published_at TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def save_to_db(conn, news_data):
    """
    將單筆新聞資料寫入資料庫
    """
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO news 
            (source, title, link, original_text, summary, category, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            news_data.get('Source', '未知'),
            news_data.get('Title', ''),
            news_data.get('Link', ''),
            news_data.get('Original Text', ''),
            news_data.get('Summary', ''),
            news_data.get('Category', '未分類'),
            news_data.get('Published Date', '')
        ))
        conn.commit()
        return cursor.rowcount > 0 # 回傳是否有新增資料 (如果 link 重複會 ignore，rowcount 為 0)
    except Exception as e:
        print(f"資料庫寫入錯誤: {e}")
        return False

def parse_ai_response(response_text):
    """
    簡單解析 AI 回傳的字串，分離出「分類」與「完整摘要」
    """
    if not response_text:
        return "未分類", ""
        
    lines = response_text.strip().split('\n')
    category = "未分類"
    summary_lines = []
    
    for line in lines:
        # 尋找第一行的 "分類：" 或 "分類:" 來抓取括號內的類別
        if "分類" in line and ("[" in line or "【" in line):
            # 簡單的方法：直接把有 "分類" 的這一行當作 category 存起來
            category = line.replace("分類：", "").replace("分類:", "").strip()
        else:
            summary_lines.append(line)
            
    summary = '\n'.join(summary_lines).strip()
    return category, summary

def main():
    print("="*60)
    print("啟動【失智症新聞自動導航員】資料管線...")
    print("="*60)
    
    # 1. 初始化資料庫
    db_path = "output/dementia_news.db"
    if not os.path.exists("output"):
        os.makedirs("output")
        
    conn = init_db(db_path)
    print(f"✅ 資料庫已連線: {db_path}")
    
    all__news = []
    
    # 2. 執行各個爬蟲收集資料
    print("\n--- 第一步：開始蒐集各來源新聞 ---")
    
    # A. Google News
    google_news = fetch_google_news(keyword="失智症", max_items=2)
    for q in google_news:
         q['Source'] = "Google News"
    all__news.extend(google_news)
    
    # B. 國內新聞 (Yahoo 健康 RSS)
    domestic_news = fetch_domestic_health_news()
    # 為了測試，只取前 2 筆
    all__news.extend(domestic_news[:2])
    
    print(f"\n📦 共收集到 {len(all__news)} 篇待處理新聞。")
    
    # 3. 逐一讓 AI 進行摘要與分類，並存入資料庫
    print("\n--- 第二步：AI 處理與資料庫存檔 ---")
    
    new_records_count = 0
    
    for i, news in enumerate(all__news):
        print(f"\n處理第 {i+1}/{len(all__news)} 篇: {news['Title']}")
        
        # 針對沒有實際內文的 RSS 新聞，我們先用標題假裝成內文來讓 AI 給出初步摘要測試
        pseudo_content = f"標題：{news['Title']}"
        if "Content_Preview" in news:
            pseudo_content += f"\n內文摘要：{news['Content_Preview']}"
            
        print("🤖 呼叫 Gemini AI 進行分析...")
        ai_response = generate_news_summary(pseudo_content, url=news['Link'])
        
        if ai_response:
             category, formatted_summary = parse_ai_response(ai_response)
             
             # 準備寫入資料庫的物件
             db_record = {
                 "Source": news.get("Source", "Unknown"),
                 "Title": news["Title"],
                 "Link": news["Link"],
                 "Original Text": pseudo_content, # 未來實作完整網頁爬蟲後，這裡放入全文
                 "Summary": formatted_summary,
                 "Category": category,
                 "Published Date": news.get("Published Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
             }
             
             is_new = save_to_db(conn, db_record)
             if is_new:
                 print(f"💾 成功寫入資料庫 (分類: {category})")
                 new_records_count += 1
             else:
                 print(f"⏩ 資料已存在於資料庫，跳過。")
                 
        # 避免 API 呼叫太頻繁被限制
        time.sleep(2)
        
    print("="*60)
    print(f"🎉 管線執行完畢。本次新增了 {new_records_count} 筆記錄到資料庫中。")
    print("="*60)
    
    conn.close()

if __name__ == "__main__":
    main()
