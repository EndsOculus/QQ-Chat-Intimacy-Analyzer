"""
main.py
--------
主程序：从未加密的 SQLite 数据库中提取指定群聊数据，进行数据清洗、计算用户互动指标，
生成 CSV 结果和图表（雷达图、条形图、指标对比图）。
支持：
  - 用户名映射文件（user_names.json），若不提供则使用数据库中的昵称。
  - 指定特定用户（focus_user 参数），仅计算该用户与其他人的互动。
  - 分析模式：群聊 (group) 或 私聊 (c2c)。
  - 多进程加速计算。
  - 可交互输入时间段，格式为 YYYY/MM/DD；若不输入则默认使用所有数据。
所有注释均为中文，确保中英文数字正确显示，删除特殊 Unicode 字符。
"""

import argparse
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from extract_chat_data import extract_chat_data
from clean_chat_data import clean_chat_data
from intimacy_analysis import calculate_intimacy_metrics
from visualization import plot_radar_multi, plot_bar_chart, plot_comparison

def input_time(prompt):
    """
    交互式输入时间，格式应为 YYYY/MM/DD，若直接回车则返回 None。
    """
    s = input(prompt).strip()
    if s == "":
        return None
    try:
        return pd.to_datetime(s, format="%Y/%m/%d")
    except Exception as e:
        print(f"[WARN] 时间格式错误：{e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="QQ 聊天记录互动亲密度分析工具")
    parser.add_argument("--group", type=int, required=True, help="指定群聊号码，例如951628619")
    parser.add_argument("--db", type=str, required=True, help="数据库文件路径，例如 nt_msg.clean.db")
    parser.add_argument("--usermap", type=str, default=None, help="用户名映射文件路径（JSON格式），可选")
    parser.add_argument("--mode", type=str, choices=["c2c", "group"], default="group", help="分析模式：c2c (私聊) 或 group (群聊)")
    parser.add_argument("--id", type=str, default=None, help="当 mode 为 group 时，指定群号；mode 为 c2c 时指定好友QQ号")
    parser.add_argument("--focus-user", type=str, default=None, help="可选，指定单个用户的QQ号，仅计算该用户与其他人的互动")
    parser.add_argument("--top-n", type=int, default=30, help="条形图显示前 top_n 对用户（最多30对）")
    parser.add_argument("--font", type=str, default="Microsoft YaHei", help="中文字体名称，例如 Microsoft YaHei 或 SimHei")
    args = parser.parse_args()

    # 设置 Matplotlib 字体，确保中英文和数字正常显示
    plt.rcParams['font.sans-serif'] = [args.font, "Arial"]
    plt.rcParams['axes.unicode_minus'] = False

    group_id = args.group
    db_path = args.db

    # 加载用户名映射文件（如果提供）
    user_map = {}
    if args.usermap:
        try:
            with open(args.usermap, "r", encoding="utf-8") as f:
                user_map = json.load(f)
        except Exception as e:
            print(f"[WARN] 加载用户名映射文件失败：{e}")

    print("正在提取数据...")
    df = extract_chat_data(db_path, group_id)
    if df.empty:
        print("[ERROR] 未提取到数据，程序退出。")
        return
    print(f"提取到 {len(df)} 条消息记录。")

    print("正在清洗数据...")
    df = clean_chat_data(df)

    # 交互输入时间段
    print("请输入时间段进行数据筛选（格式为 YYYY/MM/DD），直接回车表示不限制：")
    start_time = input_time("请输入起始日期（例如 2024/01/01）：")
    end_time = input_time("请输入结束日期（例如 2024/12/31）：")
    if start_time is not None:
        df = df[df['timestamp'] >= start_time]
        print(f"筛选后，数据起始日期为：{start_time.date()}，剩余 {len(df)} 条记录。")
    if end_time is not None:
        df = df[df['timestamp'] <= end_time]
        print(f"筛选后，数据截止日期为：{end_time.date()}，剩余 {len(df)} 条记录。")
    if df.empty:
        print("[ERROR] 筛选后的数据为空，请检查时间范围。")
        return

    # 模式选择：若 mode 为 c2c 且提供 id，则仅保留与该好友相关数据
    if args.mode == "c2c" and args.id:
        df = df[df["sender_id"].isin([args.id])]
        print(f"筛选后，仅保留与好友 {args.id} 的消息记录，共 {len(df)} 条。")

    focus_user = int(args.focus_user) if args.focus_user else None

    print("正在计算互动指标...")
    metrics_df = calculate_intimacy_metrics(df, user_name_map=user_map, focus_user=focus_user)
    if metrics_df.empty:
        print("[ERROR] 计算结果为空，程序退出。")
        return

    output_csv = f"intimacy_{group_id}.csv"
    metrics_df.to_csv(output_csv, index=False, encoding="gbk")
    print(f"指标结果已保存到 {output_csv}")

    print("正在生成图表...")
    # 绘制多对雷达图（显示前5对用户）
    top_pairs = metrics_df.head(5)
    plot_radar_multi(top_pairs, output_prefix="radar_chart_multi")
    # 绘制条形图（显示前 top_n 对用户）
    plot_bar_chart(metrics_df, top_n=args.top_n, group_id=group_id, output_prefix="bar_chart")
    # 绘制指标对比图（对比综合得分最高的一对用户）
    top_pair = metrics_df.iloc[0]
    plot_comparison(top_pair, output_prefix="comparison_chart")
    print("所有图表生成完毕。")

if __name__ == "__main__":
    main()
