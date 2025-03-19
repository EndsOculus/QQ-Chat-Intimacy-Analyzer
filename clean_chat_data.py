"""
clean_chat_data.py
------------------
数据清洗模块：
  - 删除 sender_id 或消息内容为空的记录
  - 将 sender_id 转换为字符串
  - 清除 sender_nickname 和 content 中的特殊 Unicode 字符：
      包括方向控制符、零宽字符、BOM、Emoji（如RIBBON、FISH CAKE、SUNFLOWER等）以及韩文填充字符
  - 去除 sender_nickname 中括号内的附加信息（如 QQ 号或邮箱）
  - 删除 sender_nickname 为空或者仅包含空格的记录
"""

import re
import pandas as pd

def clean_text(text: str) -> str:
    """
    清除文本中的特殊 Unicode 字符。
    
    1. 去除方向控制符、零宽字符和字节顺序标记。
    2. 去除 Emoji 表情（范围大致为 U+1F300-U+1F6FF 和 U+1F900-U+1F9FF）。
    3. 去除韩文填充字符（U+3164）。
    """
    if text is None:
        return ""
    # 去除方向控制字符、零宽字符、BOM 等
    pattern1 = r'[\u200E\u200F\u202A-\u202E\u2066-\u2069\u200B\uFEFF]'
    text = re.sub(pattern1, '', text)
    # 去除 Emoji 表情（常见 Emoji 范围）
    pattern2 = r'[\U0001F300-\U0001F6FF\U0001F900-\U0001F9FF]'
    text = re.sub(pattern2, '', text)
    # 去除韩文填充字符 (通常 U+3164)
    pattern3 = r'[\u3164]'
    text = re.sub(pattern3, '', text)
    return text

def strip_id_from_name(name: str) -> str:
    """
    如果昵称中包含括号，且括号内有非空内容，则返回括号前的部分，
    否则直接返回原始昵称（去除前后空白）。
    例如：
      "Sharen2020(2232021467)" -> "Sharen2020"
      "Alice" -> "Alice"
      "  " -> "  "（不进行过滤）
    """
    # 去除前后空白
    name = name.strip()
    if not name:
        return name
    # 使用非贪婪匹配，允许括号前后有空格
    m = re.match(r'^(.*?)\s*\(([^)]+)\)\s*$', name)
    if m and m.group(2).strip():
        return m.group(1).strip()
    else:
        return name

def clean_chat_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗聊天数据：
      1. 删除 sender_id 或 content 为空的记录。
      2. 将 sender_id 转换为字符串。
      3. 清除 sender_nickname 和 content 中的特殊 Unicode 字符（包括 Emoji 和韩文填充字符）。
      4. 去除 sender_nickname 中括号内的附加信息。
      5. 删除 sender_nickname 为空或仅包含空格的记录。
    
    参数：
        df: 原始聊天数据 DataFrame，必须包含 'sender_id', 'sender_nickname', 'content' 字段。
    
    返回：
        清洗后的 DataFrame。
    """
    # 删除 sender_id 或 content 为空的记录
    df = df.dropna(subset=['sender_id', 'content']).copy()
    df = df[~df['sender_id'].isin(['2854196310', '10000'])]


    # 将 sender_id 转换为字符串
    df['sender_id'] = df['sender_id'].astype(str)

    # 清洗 sender_nickname 和 content 中的特殊字符
    df['sender_nickname'] = df['sender_nickname'].astype(str).apply(clean_text)
    df['content'] = df['content'].astype(str).apply(clean_text)

    # 去除 sender_nickname 中括号内的附加信息（如 QQ 号或邮箱）
    df['sender_nickname'] = df['sender_nickname'].apply(strip_id_from_name)

    # 删除 sender_nickname 为空或仅包含空格的记录
    df = df[df['sender_nickname'].str.strip() != '']

    return df

if __name__ == "__main__":
    # 测试代码：假设 test.csv 包含 sender_id, sender_nickname, content 字段
    try:
        df_test = pd.read_csv("test.csv")
        df_clean = clean_chat_data(df_test)
        print("清洗后的数据预览：")
        print(df_clean.head())
    except Exception as e:
        print(f"测试数据加载或处理出错: {e}")
