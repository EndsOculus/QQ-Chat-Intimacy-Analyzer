# QQ 群聊互动亲密度分析工具

本项目提供一个用于分析 QQ 群聊中用户互动亲密度的工具。  
工具从未加密的 SQLite 数据库中提取聊天记录，经过数据清洗、归一化处理后，计算每对用户之间的互动指标，并结合各项指标的权重计算出综合亲密度得分。最后，工具将结果以 CSV 文件形式输出，并生成雷达图、条形图以及指标对比图，直观展示用户之间的互动情况。

## 特性

- **数据提取与清洗**  
  - 从 SQLite 数据库中提取群聊数据（支持群聊和私聊模式）  
  - 自动排除 QQ 号为系统消息的用户（如 10000 和 2854196310）  
  - 支持同时提取群昵称和 QQ 名称，默认以群昵称为准，若为空则使用 QQ 名称  
  - 清洗特殊 Unicode 字符、Emoji 以及韩文填充字符，确保中英文数字正常显示

- **互动指标计算**  
  - 计算平均响应时间、聊天频率、互动持续度、互惠程度、消息长度、回复次数和对话延续性  
  - 支持自定义权重，默认权重为：  
    - 平均响应时间：20%  
    - 聊天频率：20%  
    - 互动持续度：15%  
    - 互惠程度：10%  
    - 消息长度：10%  
    - 回复次数：20%  
    - 对话延续性：5%  
  - 针对低活跃群聊引入整体活跃度惩罚因子，保证结果更真实

- **多进程加速**  
  - 使用 Python 内置多进程模块加速用户对之间指标的计算，适用于 Python 3.13

- **图表展示**  
  - 生成雷达图展示各项归一化指标的分布情况  
  - 生成条形图展示群聊中亲密度最高的用户对，图表高度自适应最多显示 20 对数据  
  - 生成指标对比图，直观对比综合得分最高的用户对在各项指标上的表现  
  - 图表中用户名称格式统一为 “姓名\<QQ号\>”，邮箱部分会被自动去除；若名称较长，则图例自动采用较小字体显示

- **时间段筛选**  
  - 交互式输入起始和结束日期，支持仅输入起始日期（表示从该日期开始）或仅输入结束日期（表示截止至该日期），默认不输入则分析所有数据

## 安装方法

1. **克隆项目**  
   ```bash
   git clone https://github.com/yourusername/QQ-Chat-Intimacy-Analyzer.git
   cd QQ-Chat-Intimacy-Analyzer
   ```

2. **安装依赖**  
   本项目依赖 Python 3.13 及以下包：
   - pandas
   - numpy
   - matplotlib  
   
   你可以使用 pip 进行安装：
   ```bash
   pip install pandas numpy matplotlib
   ```

## 使用方法

### 数据准备
- 确保你的数据库文件（例如 `nt_msg.clean.db`）为未加密的 SQLite 数据库，且数据库中有表 `group_msg_table`，并包含如下字段：
  - "40027"：群聊号码
  - "40033"：发送者 QQ 号
  - "40090"：群昵称
  - "40093"：QQ 名称
  - "40050"：发送时间（Unix 时间戳，单位秒）
  - "40080"：消息内容
  - "40011"、"40012" 用于判断消息类型（这里只提取普通文本消息）
- 解密方法详见[此处](https://github.com/QQBackup/qq-win-db-key/issues/50)
- 如有需要，创建一个 `user_names.json` 文件，用于自定义用户显示名称：
  ```json
  {
    "12345678": "灵梦",
    "10101010": "魔理沙"
  }
  ```

### 运行示例

#### 分析整个群聊（如群号 98765432）的数据
```bash
python main.py --group 98765432 --db nt_msg.clean.db --mode group --id 98765432 --font "Microsoft YaHei"
```

#### 分析特定用户（如 QQ 号 12345678）与他人的互动数据
```bash
python main.py --group 98765432 --db nt_msg.clean.db --focus-user 12345678 --mode group --id 98765432 --font "Microsoft YaHei"
```

#### 交互式时间筛选
程序运行后，会提示输入起始和结束日期：
- 如果你输入“2024/01/01”后回车，再输入“2024/12/31”后回车，则只分析 2024 年的数据。
- 如果直接回车，则默认分析所有数据；
- 如果只输入起始日期，则表示从该日期开始分析；
- 如果只输入结束日期，则表示截止至该日期。

### 输出结果
- **CSV 文件**：如 `intimacy_114514191.csv`，包含各用户对的互动指标及综合亲密度得分。
- **图表文件**：  
  - `radar_chart_multi.png`：雷达图  
  - `bar_chart.png`：条形图  
  - `comparison_chart.png`：指标对比图

## 项目结构

```
qq-intimacy-analysis/
├── extract_chat_data.py        # 数据提取模块
├── clean_chat_data.py          # 数据清洗模块
├── intimacy_analysis.py        # 互动指标计算及亲密度得分模块
├── visualization.py            # 图表生成模块
├── main.py                     # 程序入口，集成各模块
├── user_names.json             # 用户名映射文件（可选）
└── README.md                   # 本文档
```

## 注意事项

- 请确保数据库文件的表结构和字段名称与代码中的查询一致；如有不同，请相应调整 SQL 查询语句。  
- 低活跃群聊中（如班级群）会采用整体活跃度惩罚因子，使得即使其他指标满分，综合得分也能较低，从而更真实反映互动情况。  
- 本项目使用多进程加速计算，建议在 CPU 核心较多的机器上运行，以提高计算效率。  
- 图表显示中，为保证中英文正确显示，请确保系统中安装了对应的中文字体（例如 Microsoft YaHei）。

## 许可证

MIT License

## 作者

由 [EndsOculus] 创建

## 鸣谢

- [pandas](https://pandas.pydata.org/)
- [numpy](https://numpy.org/)
- [matplotlib](https://matplotlib.org/)
- [Python](https://www.python.org/)
- [@F1](https://github.com/F1Justin)
- [qq-win-db-key](https://github.com/QQBackup/qq-win-db-key)