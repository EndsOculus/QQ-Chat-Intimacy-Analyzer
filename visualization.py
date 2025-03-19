"""
visualization.py
----------------
负责生成图表，包括：
  - 雷达图：展示多个用户对归一化指标（响应时间、聊天频率、互动持续度、互惠程度、消息长度、回复次数、对话延续性）的分布情况，并使用不同颜色区分。
  - 条形图：展示亲密度最高的若干对用户，标签以“姓名<QQ号> - 姓名<QQ号>”格式显示，支持设置最多显示的对数（top_n）。
  - 指标对比图：对比一对用户在部分指标（平均响应时间、平均消息长度、回复次数）上的差异。
所有图表均保存为 PNG 图片文件。
"""

import matplotlib.pyplot as plt
import numpy as np
import re

# 配置 Matplotlib 支持中英文和数字显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

def clean_text(text):
    """
    清除文本中的特殊 Unicode 控制字符。
    """
    return re.sub(r'[\u200E\u200F\u202A-\u202E]', '', str(text))

def remove_email(text):
    """
    删除文本中邮箱部分，例如 "f1<f1justin@qq.com>" 返回 "f1"。
    """
    return re.sub(r'<[^>]+>', '', str(text)).strip()

def format_label(name, uid):
    """
    格式化用户显示名称，格式为 “姓名<QQ号>”。
    同时对名称进行清洗，去除邮箱部分。
    """
    return f"{clean_text(name)}<{uid}>"

def plot_radar_multi(pairs_df, output_prefix="radar_chart_multi"):
    """
    绘制雷达图，展示多用户对各项归一化指标的分布情况。
    
    参数：
      pairs_df (DataFrame): 每行代表一对用户，要求包含以下归一化指标字段：
         'norm_avg_response_time', 'norm_chat_frequency', 'norm_interaction_continuity',
         'norm_reciprocity', 'norm_message_length', 'norm_reply_count', 'norm_dialogue_continuity'
         以及 'name1', 'name2', 'user1', 'user2' 字段。
      output_prefix (str): 输出文件前缀，生成文件名为 "{output_prefix}.png"。
    """
    if pairs_df.empty:
        print("[WARN] 无数据绘制雷达图。")
        return
    # 定义指标标签（回复次数替代@次数）
    labels = ['响应时间', '聊天频率', '互动持续度', '互惠程度', '消息长度', '回复次数', '对话延续性']
    labels = [clean_text(label) for label in labels]
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)
    angles = np.concatenate((angles, [angles[0]]))  # 闭合
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    cmap = plt.cm.get_cmap('tab10', len(pairs_df))
    for i, (_, row) in enumerate(pairs_df.iterrows()):
        values = [
            row.get('norm_avg_response_time', 0),
            row.get('norm_chat_frequency', 0),
            row.get('norm_interaction_continuity', 0),
            row.get('norm_reciprocity', 0),
            row.get('norm_message_length', 0),
            row.get('norm_reply_count', 0),
            row.get('norm_dialogue_continuity', 0)
        ]
        values += values[:1]
        color = cmap(i)
        # 格式化显示名称：去除邮箱部分，并以“姓名<QQ号>”格式显示
        name1 = remove_email(row.get('name1', ''))
        name2 = remove_email(row.get('name2', ''))
        label = f"{format_label(name1, row.get('user1', ''))} - {format_label(name2, row.get('user2', ''))}"
        ax.plot(angles, values, marker='o', linewidth=2, label=label, color=color)
        ax.fill(angles, values, alpha=0.25, color=color)
    ax.set_thetagrids(angles[:-1] * 180/np.pi, labels)
    ax.set_rlim(0, 1)
    ax.set_title("多用户对互动指标雷达图", fontsize=14)
    # legend 设置较小字体，避免过长标签挤占空间
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), prop={'size': 8})
    plt.tight_layout()
    output_file = f"{output_prefix}.png"
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"[INFO] 雷达图已保存: {output_file}")

def plot_bar_chart(metrics_df, top_n=20, group_id=None, output_prefix="bar_chart"):
    """
    绘制条形图，展示亲密度最高的前 top_n 对用户。
    
    参数：
      metrics_df (DataFrame): 包含 'name1', 'name2', 'user1', 'user2' 和 'closeness_score' 字段。
      top_n (int): 显示前 top_n 对用户，默认 20 对。
      group_id: 群号（可选），用于图表标题。
      output_prefix (str): 输出文件前缀。
    """
    df = metrics_df[metrics_df['closeness_score'] > 0].copy().head(top_n)
    if df.empty:
        print("[WARN] 没有有效数据绘制条形图。")
        return
    labels = [f"{format_label(remove_email(str(row['name1'])), row['user1'])} - {format_label(remove_email(str(row['name2'])), row['user2'])}" for _, row in df.iterrows()]
    scores = df['closeness_score']
    # 自适应高度：每对占 0.5 英寸，最小高度为 5 英寸
    fig_height = max(5, len(df) * 0.5)
    plt.figure(figsize=(10, fig_height))
    plt.barh(labels, scores, color='skyblue')
    plt.xlabel('综合亲密度评分')
    title = f"群 {group_id} 亲密度排行" if group_id else "亲密度排行"
    plt.title(title)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    output_file = f"{output_prefix}.png"
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"[INFO] 条形图已保存: {output_file}")

def plot_comparison(top_pair, output_prefix="comparison_chart"):
    """
    绘制指标对比图，对比一对用户在部分指标上的表现。
    
    参数：
      top_pair (Series): 包含以下字段：
         'resp_time_1_to_2', 'resp_time_2_to_1', 'avg_len_user1', 'avg_len_user2', 'reply_count',
         以及 'name1', 'name2', 'user1', 'user2'
      output_prefix (str): 输出文件前缀。
    """
    labels = ['平均响应时间(s)', '平均消息长度', '回复次数']
    labels = [clean_text(label) for label in labels]
    user1_val = top_pair.get('resp_time_2_to_1', 0)
    user2_val = top_pair.get('resp_time_1_to_2', 0)
    user1_values = [
        user1_val,
        top_pair.get('avg_len_user1', 0),
        top_pair.get('reply_count', 0)
    ]
    user2_values = [
        user2_val,
        top_pair.get('avg_len_user2', 0),
        top_pair.get('reply_count', 0)
    ]
    x = np.arange(len(labels))
    width = 0.35
    plt.figure(figsize=(8, 5))
    plt.bar(x - width/2, user1_values, width, label=format_label(remove_email(top_pair.get('name1', '用户1')), top_pair.get('user1', '')))
    plt.bar(x + width/2, user2_values, width, label=format_label(remove_email(top_pair.get('name2', '用户2')), top_pair.get('user2', '')))
    plt.xticks(x, labels, rotation=45)
    plt.ylabel('值')
    title = f"{format_label(remove_email(top_pair.get('name1', '用户1')), top_pair.get('user1', ''))} vs {format_label(remove_email(top_pair.get('name2', '用户2')), top_pair.get('user2', ''))} 指标对比"
    plt.title(clean_text(title))
    plt.legend(prop={'size': 8})
    plt.tight_layout()
    output_file = f"{output_prefix}.png"
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"[INFO] 指标对比图已保存: {output_file}")
