import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# 定义词云中的文字内容
# text = """
# Python is an interpreted, high-level and general-purpose programming language.
# Python's design philosophy emphasizes code readability with its notable use of significant indentation.
# Its language constructs and object-oriented approach aim to help programmers write clear, logical code for small and large-scale projects.
# Python is dynamically-typed and garbage-collected.
# """
text = """
Communication  
Collaboration  
Trust  
Respect  
Leadership  
Empathy  
Flexibility  
Motivation  
Support  
Conflict  
Creativity  
Accountability  
Feedback  
Dependability  
Initiative  
Positivity  
Adaptability  
Reliability  
Listening  
Teamwork  
Inclusivity  
Transparency  
Responsiveness  
Patience  
Compromise  
Networking  
Encouragement  
Goal-setting  
Decision-making  
Influence  
Engagement  
Vision  
Cohesion  
Synergy  
Mindfulness  
Resourcefulness  
Integrity  
Diversity  
Strategy  
Mentorship  
Trustworthiness  
Commitment  
Collaboration  
Time  
Emotional  
Relationships
JE, JE, JE
Feishu, Feishu
Github
Gantt
OKR, OKR
"""

# 创建一个圆形的遮罩
x, y = np.ogrid[:2000, :2000]  # 增加遮罩尺寸
mask = (x - 1000) ** 2 + (y - 1000) ** 2 > 980 ** 2  # 调整圆的半径
mask = 255 * mask.astype(int)

# 生成词云
wordcloud = WordCloud(
    background_color="white",
    mask=mask,
    width=2000,  # 增加图像宽度
    height=2000,  # 增加图像高度
    max_words=500,  # 增加显示的单词数量
    relative_scaling=0.5,  # 控制词语的相对大小
#    colormap='plasma',  # 使用鲜艳的颜色映射
#    colormap='inferno',  # 使用鲜艳的颜色映射
    colormap='Set1',  # 使用鲜艳的颜色映射
    font_path=None,  # 可以指定字体文件路径，如有需要
).generate(text)

# 显示词云
plt.figure(figsize=(20, 20))  # 设置图像大小
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.show()

