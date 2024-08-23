"""
 Function: Parse the bib file, query the citations, and output the xlsx file.
 Usage   : python3 bibParse.py xxx.bib yyy.xlsx
"""
import requests
import json
import bibtexparser
import openpyxl
import sys

# 函数：查询文献被引用次数
def get_citation_count(title):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        'query': title,
        'fields': 'title,citationCount',
        'limit': 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0].get('citationCount', 0)
    return 0

if len(sys.argv) < 1:
    bib = "references.bib"
else:
	bib = sys.argv[1]

if len(sys.argv) < 2:
	xlsx = "output.xlsx"
else:
    xlsx = sys.argv[2]

# 读取.bib文件
with open(bib, 'r') as bib_file:
    bib_database = bibtexparser.load(bib_file)

print(f"Excel file {bib} has been read.")

# 创建Excel文件
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Citations"
ws.append(["Title", "Year", "First Author", "Journal", "Citations"])

i = 1

# 遍历.bib中的每篇文献
for entry in bib_database.entries:
    title = entry.get('title', 'N/A')
    year = entry.get('year', 'N/A')
    author = entry.get('author', 'N/A').split(' and ')[0]  # 取第一个作者
    journal = entry.get('journal', 'N/A')
    
    print(f"Querying {i} entry...")

    # 获取被引用次数
    citations = get_citation_count(title)
    
    # 将信息写入Excel文件
    ws.append([title, year, author, journal, citations])

    i += 1

# 保存Excel文件
wb.save(xlsx)

print(f"Excel file {xlsx} has been created.")

