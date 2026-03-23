import requests
import urllib3
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os

# 目標：從台大老師網站 (陳老師) 抓取資料
# 網址：https://homepage.ntu.edu.tw/~karenchen/index_tw.html

def fetch_ntu_karenchen_news():
    """
    從台大陳老師網站抓取最新消息或文章
    """
    url = "https://homepage.ntu.edu.tw/~karenchen/index_tw.html"
    print(f"正在抓取台大老師網站: {url} ...")
    
    try:
        # 設定 headers 偽裝成瀏覽器，避免被阻擋
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 禁用 SSL 警告
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 為了正確處理中文編碼，特別標示 encoding，加上 verify=False 忽略憑證錯誤
        response = requests.get(url, headers=headers, verify=False)
        response.encoding = 'utf-8' 
        
        if response.status_code != 200:
            print(f"❌ 網站連線失敗，狀態碼: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = []
        
        # TODO: 這裡需要根據實際網頁結構進行解析
        # 由於目前尚未確認網頁的具體 HTML 結構，我們先嘗試抓取所有的段落或特定標籤
        # 例如：假設最新消息放在某個特定的 div 中，或者直接抓取所有的 h2, h3 標籤
        
        # 先簡單嘗試印出網頁標題和一些文字來確認抓取成功
        print(f"網頁標題: {soup.title.string if soup.title else '無標題'}")
        
        # 將整頁文字稍微清理後回傳，作為第一版簡單的「文章內容」
        # 實際應用中應該要精確定位到「消息」或「文章」的區塊
        
        # 假設整個網頁就是一篇介紹或文章
        content = soup.get_text(separator='\n', strip=True)
        # 取前 5000 字作為預覽
        preview = content[:5000] + "..." if len(content) > 5000 else content
        
        news_data = {
            "Title": soup.title.string if soup.title else "台大老師網站更新",
            "Link": url,
            "Published Date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # 網站可能沒時間，先用抓取當下時間
            "Content_Preview": preview
        }
        news_list.append(news_data)
        
        print("✅ 成功抓取台大老師網站基本資訊。")
        return news_list
        
    except Exception as e:
        print(f"❌ 抓取過程中發生錯誤: {e}")
        return []

if __name__ == "__main__":
    news_data = fetch_ntu_karenchen_news()
    
    if news_data:
        df = pd.DataFrame(news_data)
        
        if not os.path.exists("output"):
            os.makedirs("output")
            
        csv_path = "output/ntu_karenchen_test.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n✅ 測試成功！資料已儲存至 {csv_path}")
        print("\n預覽內容：")
        print(news_data[0]['Content_Preview'])
