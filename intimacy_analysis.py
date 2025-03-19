"""
intimacy_analysis.py
--------------------
根据清洗后的聊天数据 DataFrame 计算用户之间的互动亲密度指标。

计算指标包括：
  - 平均响应时间：计算两人交替发言的平均时间间隔（秒），值越小越好（归一化时取反）。
  - 聊天频率：单位天内的消息数。
  - 互动持续度：连续互动（消息间隔 ≤ 60 秒）的平均往返次数。
  - 互惠程度：双方发言数的比例（较小者/较大者）。
  - 消息长度：双方消息的平均字符数。
  - 回复次数：交替回复的次数。
  - 对话延续性：一方发言后 60 秒内对方回复的比例。

所有指标归一化后，根据预设权重计算综合亲密度得分，并增加整体活跃度惩罚因子：
如果整个群聊消息数低于 1000，则综合得分乘以 (总消息数/1000)。

支持多进程加速计算，适用于 Python 3.13。
"""

# 定义各指标权重，总和为1
WEIGHTS = {
    "avg_response_time": 0.20,
    "chat_frequency": 0.20,
    "interaction_continuity": 0.15,
    "reciprocity": 0.10,
    "message_length": 0.10,
    "reply_count": 0.20,
    "dialogue_continuity": 0.05
}

import pandas as pd
import numpy as np
from itertools import combinations
import re
import os
import math

# 全局变量，用于多进程共享 DataFrame
_df_global = None

def _init_pool(dataframe):
    """在多进程池中初始化全局 DataFrame"""
    global _df_global
    _df_global = dataframe

def compute_at_count(pair_df, uid1, uid2, name1, name2):
    """
    统计 @ 互动次数（此函数已不再使用，改为回复次数统计）。
    """
    return 0, 0, 0

def _compute_pair_metrics(pair):
    """
    计算单对用户的所有互动指标，用于多进程并行计算。

    参数：
        pair: 一个元组 (uid1, uid2)
    返回：
        一个字典，包含 uid1, uid2, name1, name2 以及各项指标；
        如果某一用户没有消息，则返回 None。
    """
    uid1, uid2 = pair
    df = _df_global  # 使用全局 DataFrame
    pair_df = df[df['sender_id'].isin([uid1, uid2])].copy()
    pair_df.sort_values('timestamp', inplace=True)
    if pair_df.empty:
        return None

    # 检查 uid1 和 uid2 是否各自存在消息
    df_uid1 = pair_df[pair_df['sender_id'] == uid1]
    df_uid2 = pair_df[pair_df['sender_id'] == uid2]
    if df_uid1.empty or df_uid2.empty:
        return None

    # 获取用户昵称
    try:
        name1 = df_uid1['sender_nickname'].iloc[0]
        name2 = df_uid2['sender_nickname'].iloc[0]
    except IndexError:
        return None

    # --- 计算响应时间 ---
    times = pair_df['timestamp'].apply(lambda t: t.timestamp()).tolist()
    senders = pair_df['sender_id'].tolist()
    response_times = []       # 所有交替发言的时间间隔
    reply_count = 0           # 回复次数：即交替回复次数
    resp_times_1_to_2 = []    # uid1 发言后 uid2 回复时间
    resp_times_2_to_1 = []    # uid2 发言后 uid1 回复时间
    for i in range(1, len(pair_df)):
        if senders[i] != senders[i-1]:
            dt = times[i] - times[i-1]
            response_times.append(dt)
            reply_count += 1
            if senders[i-1] == uid1 and senders[i] == uid2:
                resp_times_1_to_2.append(dt)
            elif senders[i-1] == uid2 and senders[i] == uid1:
                resp_times_2_to_1.append(dt)
    avg_resp = float(np.mean(response_times)) if response_times else 300.0
    avg_resp_1_to_2 = float(np.mean(resp_times_1_to_2)) if resp_times_1_to_2 else 300.0
    avg_resp_2_to_1 = float(np.mean(resp_times_2_to_1)) if resp_times_2_to_1 else 300.0

    # --- 聊天频率 ---
    total_msgs = len(pair_df)
    duration_days = (pair_df['timestamp'].iloc[-1] - pair_df['timestamp'].iloc[0]).days + 1
    chat_freq = total_msgs / duration_days if duration_days > 0 else total_msgs

    # --- 互动持续度 ---
    gap_threshold = 60  # 60秒内视为连续互动
    chain_lengths = []
    current_chain = 1
    for i in range(1, len(pair_df)):
        gap = times[i] - times[i-1]
        if gap <= gap_threshold and senders[i] != senders[i-1]:
            current_chain += 1
        else:
            chain_lengths.append(current_chain)
            current_chain = 1
    chain_lengths.append(current_chain)
    interaction_continuity = float(np.mean(chain_lengths)) if chain_lengths else 0.0

    # --- 互惠程度 ---
    count1 = (pair_df['sender_id'] == uid1).sum()
    count2 = (pair_df['sender_id'] == uid2).sum()
    reciprocity = (min(count1, count2) / max(count1, count2)) if (count1 and count2) else 0.0

    # --- 消息长度 ---
    avg_len_user1 = df_uid1['content'].astype(str).apply(len).mean() if count1 > 0 else 0.0
    avg_len_user2 = df_uid2['content'].astype(str).apply(len).mean() if count2 > 0 else 0.0
    avg_msg_length = (avg_len_user1 + avg_len_user2) / 2.0

    # --- 回复次数 ---
    reply_count = len(response_times)

    # --- 对话延续性 ---
    quick_resp_count_1 = 0  # uid2 对 uid1 的快速回复次数
    quick_resp_count_2 = 0  # uid1 对 uid2 的快速回复次数
    for i in range(1, len(pair_df)):
        if senders[i] != senders[i-1]:
            dt = times[i] - times[i-1]
            if dt <= 60:
                if senders[i-1] == uid1 and senders[i] == uid2:
                    quick_resp_count_2 += 1
                elif senders[i-1] == uid2 and senders[i] == uid1:
                    quick_resp_count_1 += 1
    ratio_1 = quick_resp_count_2 / count1 if count1 > 0 else 0.0
    ratio_2 = quick_resp_count_1 / count2 if count2 > 0 else 0.0
    dialogue_continuity = (ratio_1 + ratio_2) / 2.0

    return {
        'user1': uid1,
        'user2': uid2,
        'name1': name1,
        'name2': name2,
        'avg_response_time': avg_resp,
        'chat_frequency': chat_freq,
        'interaction_continuity': interaction_continuity,
        'reciprocity': reciprocity,
        'message_length': avg_msg_length,
        'reply_count': reply_count,
        'dialogue_continuity': dialogue_continuity,
        'count1': int(count1),
        'count2': int(count2),
        'resp_time_1_to_2': avg_resp_1_to_2,
        'resp_time_2_to_1': avg_resp_2_to_1,
        'avg_len_user1': avg_len_user1,
        'avg_len_user2': avg_len_user2
    }

def norm_response_time(rt, max_rt=300):
    return max(0, 1 - rt / max_rt)

def norm_chat_frequency(freq, threshold=0.5):
    return min(1.0, freq / threshold)

def norm_interaction_continuity(val, threshold=1):
    return min(1.0, val / threshold)

def norm_reciprocity(rec):
    return rec

def norm_message_length(length, ideal=50, width=30):
    return math.exp(-((length - ideal) / width) ** 2)

def norm_reply_count(count, threshold=5):
    return min(1.0, count / threshold)

def norm_dialogue_continuity(val, threshold=0.5):
    return min(1.0, val / threshold)

def calculate_intimacy_metrics(df: pd.DataFrame, user_name_map: dict = None, focus_user=None) -> pd.DataFrame:
    """
    计算群聊中所有用户两两之间的互动指标和综合亲密度得分。

    参数：
        df: 清洗后的聊天记录 DataFrame，必须包含 sender_id, sender_nickname, content, timestamp。
        user_name_map: 可选，用户ID到显示名称的映射字典。
        focus_user: 可选，若指定，则仅计算该用户与其他用户的互动指标。
    
    返回：
        DataFrame，每一行代表一对用户的各项指标及综合得分。
    """
    # 确保 focus_user 为字符串，与 df 中 sender_id 一致
    if focus_user is not None:
        focus_user = str(focus_user)
        user_ids = [focus_user] + [uid for uid in df['sender_id'].unique() if uid != focus_user]
        pairs = [(focus_user, uid) for uid in user_ids if uid != focus_user]
    else:
        user_ids = df['sender_id'].unique()
        pairs = list(combinations(user_ids, 2))
    if not pairs:
        return pd.DataFrame()
    
    # 以下多进程计算保持不变...
    from concurrent.futures import ProcessPoolExecutor
    cpu_count = os.cpu_count() or 1
    with ProcessPoolExecutor(max_workers=cpu_count, initializer=_init_pool, initargs=(df,)) as executor:
        results = list(executor.map(_compute_pair_metrics, pairs))
    results = [res for res in results if res is not None]
    metrics_df = pd.DataFrame(results)
    if metrics_df.empty:
        return metrics_df

    if user_name_map:
        metrics_df['name1'] = metrics_df['user1'].apply(lambda uid: user_name_map.get(str(uid), ""))
        metrics_df['name2'] = metrics_df['user2'].apply(lambda uid: user_name_map.get(str(uid), ""))
    
    # 以下归一化和权重计算部分...
    metrics_to_normalize = [
        ('avg_response_time', True),
        ('chat_frequency', False),
        ('interaction_continuity', False),
        ('reciprocity', False),
        ('message_length', False),
        ('reply_count', False),
        ('dialogue_continuity', False)
    ]
    for col, reverse in metrics_to_normalize:
        if metrics_df[col].max() != metrics_df[col].min():
            if reverse:
                metrics_df['norm_' + col] = 1 - (metrics_df[col] - metrics_df[col].min()) / (metrics_df[col].max() - metrics_df[col].min())
            else:
                metrics_df['norm_' + col] = (metrics_df[col] - metrics_df[col].min()) / (metrics_df[col].max() - metrics_df[col].min())
        else:
            metrics_df['norm_' + col] = 1.0 if metrics_df[col].iloc[0] != 0 else 0.0

    norm_cols = list(WEIGHTS.keys())
    metrics_df['closeness_score'] = metrics_df.apply(
        lambda row: sum(WEIGHTS[col] * row[f"norm_{col}"] for col in norm_cols),
        axis=1
    )
    
    # 整体活跃度惩罚因子：如果群总消息数少于 1000，则乘以 (总消息数/1000)
    total_msgs_overall = len(df)
    activity_factor = min(1.0, total_msgs_overall / 1000.0)
    metrics_df['closeness_score'] *= activity_factor

    metrics_df.sort_values('closeness_score', ascending=False, inplace=True)
    metrics_df.reset_index(drop=True, inplace=True)
    return metrics_df

if __name__ == "__main__":
    import datetime
    data = {
        'sender_id': [10000, 2232021467, 10000, 2232021467],
        'sender_nickname': ['Alice(10000)', 'Sharen2020(2232021467)', 'Alice(10000)', 'Sharen2020(2232021467)'],
        'content': ['你好', '回复：我同意', '谢谢', '回复：很好'],
        'timestamp': [
            datetime.datetime.now(),
            datetime.datetime.now() + datetime.timedelta(seconds=10),
            datetime.datetime.now() + datetime.timedelta(seconds=20),
            datetime.datetime.now() + datetime.timedelta(seconds=25)
        ]
    }
    df_test = pd.DataFrame(data)
    metrics = calculate_intimacy_metrics(df_test)
    print(metrics)
