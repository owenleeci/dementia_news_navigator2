from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os

def setup_driver():
    """初始化並設定 Selenium Chrome Driver 強制無頭模式並加入防反爬蟲參數"""
    chrome_options = Options()
    # 啟用無頭模式 (不顯示瀏覽器介面)
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # 不要載入圖片以加快速度
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    
    # 防偵測機制
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 使用最新的 Chrome 使用者代理
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 啟動時執行 JS 覆蓋 webdriver 屬性
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def fetch_lancet_with_selenium(driver):
    """
    從 The Lancet 抓取失智症相關的最新公開標題。
    """
    url = "https://www.thelancet.com/action/doSearch?text1=dementia&field1=AllField&SeriesKey=lancet"
    print(f"正在透過 Selenium 抓取 The Lancet: {url} ...")
    news_list = []
    
    try:
        driver.get(url)
        # 等待搜尋結果清單載入 (等待帶有 sr-list 相關 class 的元素)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search__item"))
        )
        # 稍微等一下確保 JavaScript 渲染完畢
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        articles = soup.find_all('li', class_='search__item')
        
        for idx, article in enumerate(articles[:5]):
             title_element = article.find('a') if article.name == 'li' else article
             if title_element:
                 title = title_element.get_text(strip=True)
                 link = title_element.get('href', '')
                 if link and not link.startswith('http'):
                     link = 'https://www.thelancet.com' + link
                 
                 news_list.append({
                     "Source": "The Lancet",
                     "Title": title,
                     "Link": link,
                     "Published Date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                 })
                 print(f"✅ Lancet 找到: {title}")
                 
    except Exception as e:
        print(f"❌ 抓取 Lancet 發生錯誤或逾時: {e}")
        
    return news_list

def fetch_nejm_with_selenium(driver):
    """
    從 NEJM 抓取失智症相關文章。
    """
    url = "https://www.nejm.org/search?q=dementia"
    print(f"\n正在透過 Selenium 抓取 NEJM: {url} ...")
    news_list = []
    
    try:
        driver.get(url)
        # NEJM 結果通常在 m-teaser 區塊中
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "m-teaser"))
        )
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 尋找所有新聞的標題 a 連結 (通常包裝在 h2 或是 h4 內)
        teasers = soup.find_all('div', class_='m-teaser')
        
        for idx, teaser in enumerate(teasers[:5]):
             title_element = teaser.find('a')
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
                 print(f"✅ NEJM 找到: {title}")
                 
    except Exception as e:
        print(f"❌ 抓取 NEJM 發生錯誤或逾時: {e}")
        
    return news_list

if __name__ == "__main__":
    driver = None
    try:
        print("啟動無頭瀏覽器...")
        driver = setup_driver()
        
        lancet_data = fetch_lancet_with_selenium(driver)
        nejm_data = fetch_nejm_with_selenium(driver)
        
        all_data = lancet_data + nejm_data
        
        if all_data:
            df = pd.DataFrame(all_data)
            if not os.path.exists("output"):
                os.makedirs("output")
            csv_path = "output/medical_journals_selenium_test.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"\n🎉 爬蟲測試成功！醫療期刊資料已儲存至 {csv_path}")
        else:
            print("\n⚠️ 雙方期刊均未抓取到資料，可能需要手動確認網頁驗證機制 (CAPTCHA)。")
            
    except Exception as e:
         print(f"執行期間發生未預期錯誤: {e}")
    finally:
        if driver:
            print("關閉瀏覽器...")
            driver.quit()
