"""
 Function: Request CoRL 2024 papers, save to excel file.
 Usage   : python3 CoRL_2024.py CoRL_papers_2024.xlsx
"""
import requests
import pandas as pd
import time
import sys

# 基础 URL 和请求参数
base_url = "https://api2.openreview.net/notes"
headers = {
    "accept": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

params = {
    "content.venue": "CoRL 2024",
    "details": "replyCount,presentation",
    "domain": "robot-learning.org/CoRL/2024/Conference",
    "limit": 25,
    "offset": 0
}

# 保存文献数据的列表
papers = []

# 爬取所有页面
while True:
    print(f"正在请求 offset={params['offset']} 的数据...")
    response = requests.get(base_url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"请求失败，状态码：{response.status_code}")
        break

    data = response.json()
    notes = data.get("notes", [])

    # 如果没有更多数据，结束循环
    if not notes:
        print("已获取所有数据！")
        break

    # 解析每篇文献
    for note in notes:
        content = note.get("content", {})
        authors = content.get("authors", {}).get("value", [])
        papers.append({
            "Title": content.get("title", {}).get("value", ""),
            "Authors": authors[0] if authors else "",
            "Keywords": ", ".join(content.get("keywords", {}).get("value", [])),
            "Abstract": content.get("abstract", {}).get("value", ""),
            "Video": content.get("video", {}).get("value", ""),
            "Website": content.get("website", {}).get("value", ""),
            "Code": content.get("code", {}).get("value", ""),
            "Original": f"https://openreview.net/forum?id={note.get('forum', '')}"
        })

    # 更新偏移量以获取下一页数据
    params["offset"] += 25
    time.sleep(5)  # 防止请求过于频繁

# 保存为 Excel 文件
df = pd.DataFrame(papers)
# output_path = "CoRL_papers_2024.xlsx"
output_path = sys.argv[1]
df.to_excel(output_path, index=False)
print(f"数据已保存到 {output_path}")

