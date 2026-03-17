import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

def generate_news_summary(article_text, url="未提供", system_instruction=None):
    """
    使用 Gemini API 對新聞內文進行摘要、格式化與分類
    """
    
    # 取得 API Key (請確保在根目錄下有一個 .env 檔案並設定 GEMINI_API_KEY)
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ 錯誤：找不到 GEMINI_API_KEY。請在 .env 檔案中設定。")
        return None
        
    try:
        # 初始化 GenAI 客戶端
        client = genai.Client(api_key=api_key)
        
        # 決定使用的模型 (建議使用最新的 gemini-2.5-flash 來平衡速度與成本)
        # 對於單純的文字總結，flash 已經非常足夠
        model_name = "gemini-2.5-flash"
        
        # 預設的 System Instruction：強制我們需要的文件格式與語氣
        if not system_instruction:
            system_instruction = """
            你現在是一個專業的「失智症新聞與醫療文獻自動導航員」。
            你的任務是閱讀使用者提供的新聞內文，並進行總結與分類。
            
            【強制輸出格式】
            請完全遵守以下五個段落的順序進行輸出，並且以「中文說明為主」，但如果原文中有非常關鍵的醫療專有名詞、藥物名稱或醫學金句，請在括號內補充英文原文，或使用英文原句輔助說明。
            如果該新聞沒有涵蓋特定的段落內容，請在該段落寫上「無相關資訊」。
            
            1. **趨勢摘要**：(30-50字的精煉核心重點)
            2. **預防**：(文章中關於如何預防失智症的建議)
            3. **早篩**：(關於早期發現與篩檢的相關資訊)
            4. **治療**：(新的療法、藥物或是照護技巧)
            5. **延伸閱讀**：(請原封不動放入此處提供的原文網址：{url})
            
            【分類標籤】
            在所有內容的最上方，請單獨用一行標示出這篇新聞所屬的類別，從以下選項中擇一：
            [醫學新知]、[照護技巧]、[社會安全與補助]、[溫馨故事]、[政策法規]、[其他]
            預期格式如： 分類：[醫學新知]
            """
            # 動態替換網址
            system_instruction = system_instruction.replace("{url}", url)
            
        print("🤖 正在呼叫 Gemini 分析新聞內容...")
        
        # 透過 types.GenerateContentConfig 設定 System Instruction
        response = client.models.generate_content(
            model=model_name,
            contents=article_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3, # 設定較低的 temperature 以確保輸出格式穩定且不亂發揮
            ),
        )
        
        return response.text
        
    except Exception as e:
        print(f"❌ AI 處理發生錯誤: {e}")
        return None

if __name__ == "__main__":
    # 測試用假新聞內文
    test_article = """
    路透社報導，美國食品藥物管理局（FDA）今日正式核准了全新阿茲海默症（Alzheimer's disease）藥物「Donanemab」。
    該藥物在第三期臨床試驗中展現了顯著的成效，特別是針對早期阿茲海默症患者，能有效減緩認知功能的衰退達35%。
    負責該研究的科學家李博士表示：「這是我們在清除大腦澱粉樣蛋白（amyloid plaque）療法上的一大突破。」
    雖然目前無法完全治癒失智症，但透過定期的腦部正子斷層造影（PET scan）進行早期篩檢，配合健康的地中海飲食（Mediterranean diet）和每週規律的有氧運動，能大大降低發病風險。
    此藥物預計下個月就會在美國納入高齡醫療保險補助範圍。
    """
    
    print("\n--- 準備測試 Gemini 摘要功能 ---")
    
    # 這個測試需要有真正的 API Key 才能成功執行
    # 為了展示，如果你剛好沒有，程式會印出提示。
    
    # 寫入一個空的 .env 檔案（如果不存在的話）方便使用者填寫
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
             f.write("GEMINI_API_KEY=在這裡填入你的金鑰\n")
        print("💡 已建立空的 .env 檔案，請填入你的 GEMINI_API_KEY 後再執行一次。")
    else:
        # 如果已經有了，就進行測試
        result = generate_news_summary(test_article, url="https://example-medical-news.com/donanemab-approval")
        if result:
            print("\n🎉 AI 成功回傳結果：\n")
            print("=" * 50)
            print(result)
            print("=" * 50)
