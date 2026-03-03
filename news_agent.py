import feedparser
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import OpenAI
from datetime import datetime

# ================= 配置区 =================
# ================= 1. 订阅的新闻源 (RSS) =================
# 使用开源的 RSSHub 节点来抓取国内无原生 RSS 的媒体
RSS_FEEDS = {
    "科技与AI": "https://www.zhihu.com/org/ji-qi-zhi-xin-65",    # 机器之心 (国内最顶尖的AI垂直媒体)
    "综合科技": "https://www.ithome.com/rss/",                   # IT之家 (国内更新极快的综合科技前沿)
    "经济金融": "https://rss.sina.com.cn/roll/finance/hot_roll.xml", # 新浪财经 (官方原生源，稳定)
    "宏观经济": "https://rsshub.app/wallstreetcn/news/global",   # 华尔街见闻-全球 (宏观经济与市场)
    "深度文化": "https://rsshub.app/jiemian/lists/45",           # 界面新闻·文化频道 (人文、书籍、社科)
    "思想市场": "https://rsshub.app/thepaper/channel/25950",     # 澎湃新闻·思想市场 (深度社会与文化评论)
}

# 2. 环境变量 (稍后在 GitHub Secrets 中配置)
API_KEY = os.getenv("sk-llumrnqosgeiusgsqrtzdutpbwmsoppqdfqiblmvpjdrkhzt") 
EMAIL_SENDER = os.getenv("plenilunesept@gmail.com")       # 你的发件 Gmail
EMAIL_PASSWORD = os.getenv("ckxvyhflilgpxnvg")   # Gmail 的应用程式密码
EMAIL_RECEIVER = os.getenv("plenilunesept@gmail.com")   # 收件邮箱 (可以是同一个)

# ================= 1. 收集新闻 =================
def fetch_news():
    news_content = ""
    for category, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            news_content += f"【{category}】\n"
            # 获取每个频道的最新 8 条供 AI 筛选 (给 AI 更多素材来挑出 AI 相关新闻)
            for entry in feed.entries[:8]:
                title = entry.title
                link = entry.link
                summary = entry.summary if 'summary' in entry else ""
                news_content += f"标题: {title}\n链接: {link}\n摘要: {summary}\n\n"
        except Exception as e:
            print(f"抓取 {category} 失败: {e}")
    return news_content

# ================= 2. AI 总结新闻 =================
def summarize_news(news_text):
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://api.siliconflow.cn/v1"
    )
    
    prompt = f"""
    你是一个资深的国内新闻主编。请阅读以下我为你抓取的今日国内新闻素材，帮我撰写一份结构清晰、深度精炼的每日简报。

    【核心筛选与排版要求】：
    1. 必须分为三个板块：🌟 科技与 AI 前沿、📈 经济与市场、📚 文化与思想。
    2. **最高优先级**：在扫读所有新闻时，一旦发现与**人工智能、大模型、AI 应用、半导体芯片**相关的新闻，请务必保留，并放在“科技与 AI 前沿”板块的最头部重点讲解。
    3. 每个板块挑选 3-4 条最具价值的新闻，忽略灌水或价值不高的重复资讯。
    4. 每条新闻格式：用一句话概括核心事件，并附上 1-2 个 Bullet points 说明其商业影响或社会意义。
    5. 每条新闻后必须附上原文链接。
    6. 语言风格：专业、客观、流畅的简体中文。

    今日新闻素材：
    {news_text}
    """
    print("正在请求 AI 进行深度筛选和总结...")
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1", # 或者 deepseek-chat
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6  # 稍微调低温度，让新闻总结更严谨客观
    )
    return response.choices[0].message.content

# ================= 3. 发送邮件 =================
def send_email(ai_summary):
    print("正在发送邮件...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"📰 你的专属 AI 早报 - {today_str}"
    
    # 转换 Markdown 为简单的 HTML，以便在邮件中更好看
    html_content = ai_summary.replace('\n', '<br>')
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    try:
        # 连接 Gmail SMTP 服务器
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        print("✅ 邮件发送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# ================= 主程序 =================
if __name__ == "__main__":
    print("Agent 开始工作...")
    raw_news = fetch_news()
    summary = summarize_news(raw_news)
    send_email(summary)

    print("Agent 工作完成！")






