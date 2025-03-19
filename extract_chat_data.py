"""
extract_chat_data.py
--------------------
从未加密的 SQLite 数据库中提取群聊数据。

要求：
- 数据库文件（如 nt_msg.clean.db）中包含表 group_msg_table，
  其中：
    - 群号存储在 "40027" 列；
    - 发送者QQ号存储在 "40033" 列；
    - 群昵称存储在 "40090" 列；
    - QQ名称存储在 "40093" 列；
    - 消息发送时间存储在 "40050" 列（Unix 时间戳，单位秒）；
    - 消息内容存储在 "40080" 列。
- 只提取文本消息，即要求 "40011" 的值为 2（文本消息）且 "40012" 的值为 1（普通文本消息）。
"""

import sqlite3
import pandas as pd

def extract_chat_data(db_path: str, group_id: int) -> pd.DataFrame:
    """
    从数据库中提取指定群聊的数据。

    参数：
        db_path: 数据库文件路径，例如 "nt_msg.clean.db"。
        group_id: 指定的群聊号码，例如 951628619 或 457747541。

    返回：
        DataFrame，包含以下字段：
          - sender_id: 发送者QQ号（字符串类型）
          - sender_nickname: 用户显示名称，优先使用群昵称（字段 "40090"），若为空则使用QQ名称（字段 "40093"）
          - content: 消息内容（文本）
          - timestamp: 消息发送时间（已转换为 datetime 格式）
    """
    try:
        conn = sqlite3.connect(db_path)
    except Exception as e:
        print(f"[ERROR] 无法连接数据库: {e}")
        return pd.DataFrame()

    # 同时提取群昵称（40090）和QQ名称（40093）
    query = f"""
    SELECT 
        "40033" AS sender_id,
        "40090" AS group_nickname,
        "40093" AS qq_name,
        "40080" AS content,
        "40050" AS timestamp
    FROM group_msg_table
    WHERE "40027" = ? 
      AND "40011" = 2 
      AND "40012" = 1 
      AND content IS NOT NULL 
      AND TRIM(content) <> ''
    """
    try:
        df = pd.read_sql_query(query, conn, params=(group_id,))
    except Exception as e:
        print(f"[ERROR] 执行 SQL 查询失败: {e}")
        conn.close()
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        print(f"[INFO] 群聊 {group_id} 未提取到有效数据。")
        return df

    # 将 sender_id 转换为字符串
    df['sender_id'] = df['sender_id'].astype(str)

    # 将 timestamp 转换为 datetime 类型（假设存储的是 Unix 时间戳，单位秒）
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    except Exception as e:
        print(f"[WARN] 时间戳转换失败: {e}")

    # 设置 sender_nickname 为群昵称，如果群昵称为空或仅为空格，则使用 QQ 名称
    df['sender_nickname'] = df['group_nickname'].fillna('').str.strip()
    df.loc[df['sender_nickname'] == '', 'sender_nickname'] = df.loc[df['sender_nickname'] == '', 'qq_name']

    # 删除多余的临时字段
    df.drop(columns=['group_nickname', 'qq_name'], inplace=True)

    return df

# 测试代码（可删除）
if __name__ == "__main__":
    db_file = "nt_msg.clean.db"
    group = 951628619
    data = extract_chat_data(db_file, group)
    print(f"提取到 {len(data)} 条消息记录")
    print(data.head())
