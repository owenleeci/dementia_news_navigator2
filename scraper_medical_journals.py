import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import urllib3
import cloudscraper

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_lancet_dementia_news():
    """
    從 The Lancet 抓取失智症相關的最新文章。
    注意：醫學期刊通常有嚴格的防爬蟲機制，這裡以抓取公開標題為主。
    """
    # 這是 Lancet 搜尋 'dementia' 的公開網址
    url = "https://www.thelancet.com/action/doSearch?text1=dementia&field1=AllField&SeriesKey=lancet"
    print(f"正在抓取 The Lancet (Dementia): {url} ...")
    
    headers = {
         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
         'Accept-Language': 'en-US,en;q=0.5',
         'Referer': 'https://www.google.com/'
    }
    
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Lancet 網站連線失敗，狀態碼: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = []
        
        # 尋找搜尋結果區塊 (The Lancet 的標題通常在具有特定 class 的 h2 或 a 標籤內)
        # 實際結構可能隨時間改變，這裡做一個初步假設
        articles = soup.find_all('li', class_='search__item')
        
        if not articles:
             print("⚠️ 未找到預期的 HTML 結構，可能網站已經改版。改用粗略搜尋 <h2> 標籤。")
             articles = soup.find_all('h2')[:5] # 若找不到，先抓 5 個 h2 標籤當作標題
        
        for idx, article in enumerate(articles[:5]): # 只取前 5 篇
             # 嘗試找到標題與連結
             title_element = article.find('a') if article.name == 'li' else article
             
             if title_element:
                 title = title_element.get_text(strip=True)
                 link = title_element.get('href', '')
                 if link and not link.startswith('http'):
                     link = 'https://www.thelancet.com' + link
                 
                 # 存入清單
                 news_list.append({
                     "Source": "The Lancet",
                     "Title": title,
                     "Link": link,
                     "Published Date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                 })
                 print(f"Lancet 標題 {idx+1}: {title}")
                 
        return news_list
        
    except Exception as e:
        print(f"❌ 抓取 Lancet 發生錯誤: {e}")
        return []

def fetch_nejm_dementia_news():
    """
    從 NEJM (The New England Journal of Medicine) 抓取失智症相關文章。
    """
    # NEJM 搜尋 'dementia' 
    url = "https://www.nejm.org/search?q=dementia"
    print(f"\n正在抓取 NEJM (Dementia): {url} ...")
    
    headers = {
         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
         'Accept-Language': 'en-US,en;q=0.5',
         'Referer': 'https://www.google.com/'
    }
    
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ NEJM 網站連線失敗，狀態碼: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = []
        
        # NEJM 搜尋結果通常在 specific list items 中
        articles = soup.find_all('li', class_='o-teaser')
        
        if not articles:
             # fallback 策略，搜尋 h4 標籤
             print("⚠️ 未找到預期的 HTML 結構，改用粗略搜尋 <h4> 標籤。")
             articles = soup.find_all('h4')[:5]
        
        for idx, article in enumerate(articles[:5]):
             title_element = article.find('a') if article.name == 'li' else article
             
             if title_element:
                 title = title_element.get_text(strip=True)
                 link = title_element.get('href', '')
                 if link and not link.startswith('http'):
                     link = 'https://www.nejm.org' + link
                 
                 news_list.append({
                     "Source": "NEJM",
                     "Title": title,
                     "Link": link,
                     "Published Date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                 })
                 print(f"NEJM 標題 {idx+1}: {title}")
                 
        return news_list
        
    except Exception as e:
        print(f"❌ 抓取 NEJM 發生錯誤: {e}")
        return []

if __name__ == "__main__":
    lancet_data = fetch_lancet_dementia_news()
    nejm_data = fetch_nejm_dementia_news()
    
    # 合併資料
    all_data = lancet_data + nejm_data
    
    if all_data:
        df = pd.DataFrame(all_data)
        if not os.path.exists("output"):
            os.makedirs("output")
        csv_path = "output/medical_journals_test.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n✅ 測試成功！醫療期刊資料已儲存至 {csv_path}")
