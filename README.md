[Click here to view the English version of the README](https://github.com/EndsOculus/QQ-Chat-Intimacy-Analyzer/blob/main/README_en.md)
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

## 各项指标解释与判定标准

本工具基于聊天记录计算下列七项指标，综合得分反映用户之间的互动亲密度。各指标的具体含义和判定标准如下：

1. **平均响应时间**  
   - **含义**：衡量两人交替发言时的平均回复间隔，时间越短表示双方回复越及时，互动越紧密。  
   - **判定标准**：  
     - **0 秒至 300 秒**：0 秒时最佳，300 秒或以上时视为回复较慢。  
     - 在归一化过程中采用公式：`得分 = max(0, 1 - (实际回复时间 / 300))`，即回复时间越低得分越高。

2. **聊天频率**  
   - **含义**：指单位时间内双方发送的消息总数，反映整体的互动活跃度。  
   - **判定标准**：  
     - 设定一个绝对阈值（例如每人每天 0.5 条消息为基准），频率低于该阈值时按比例计算得分，高于则得满分。  
     - 归一化公式示例：`得分 = min(1.0, 实际频率 / 0.5)`。

3. **互动持续度**  
   - **含义**：衡量连续互动的程度，即双方在短时间内交替对话的平均轮次。  
   - **判定标准**：  
     - 如果连续互动轮次较低（例如平均连续轮次不到 1），则说明对话断断续续；超过 1 则得分按比例提升，通常 1 轮及以上视为基本连续。

4. **互惠程度**  
   - **含义**：计算双方消息数量的平衡性，即较少一方与较多一方的消息比例。  
   - **判定标准**：  
     - 公式为：`互惠程度 = min(消息数_A, 消息数_B) / max(消息数_A, 消息数_B)`。  
     - 值越接近 1 表示双方交流较平衡，值越低则表明一方明显更活跃。

5. **消息长度**  
   - **含义**：指双方发送消息的平均字符数，反映消息内容的丰富程度。  
   - **判定标准**：  
     - 可设定一个理想的消息长度范围（例如理想值为 50 字，允许一定的浮动）。  
     - 采用非线性函数（例如高斯函数）映射实际消息长度到 0～1 之间，理想长度附近得分最高。

6. **回复次数**  
   - **含义**：统计两人交替回复的次数，是直接反映双方互动频率的重要指标。  
   - **判定标准**：  
     - 设定一个阈值（例如 5 次回复为基准），回复次数低于阈值则得分按比例计算，高于则得满分。  
     - 归一化公式示例：`得分 = min(1.0, 实际回复次数 / 5)`。

7. **对话延续性**  
   - **含义**：衡量一方发言后对方在 60 秒内进行回复的比例，反映对话是否具有连贯性。  
   - **判定标准**：  
     - 如果在一方发言后对方的快速回复（60 秒内）比例较高，则说明对话较为连贯。  
     - 可以设定阈值（例如 0.5 作为参考），按比例归一化计算。

此外，为了防止低活跃群聊（例如班级群）中除回复次数外的各项指标均趋近于满分，本工具还引入了整体活跃度惩罚因子：  
- 如果整个群聊的消息总数低于 1000，则综合得分会乘以 (总消息数 / 1000)，使得在低活跃环境下得分较低，更贴合实际情况。

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

## 参数说明及使用示例

运行程序时，请通过命令行传入以下参数：

- `--group <群号>`：指定群聊号码（必选）。
- `--db <数据库文件路径>`：指定未加密的 SQLite 数据库文件路径（必选）。
- `--mode <group|c2c>`：指定分析模式，默认为 `group`；若为 `c2c` 表示私聊模式。
- `--id <群号或好友QQ号>`：当 `--mode` 为 `group` 时传入群号；若为 `c2c` 模式则传入好友 QQ 号。
- `--focus-user <QQ号>`：可选，指定单个用户的 QQ 号，仅计算该用户与其他人的互动数据。
- `--usermap <文件路径>`：可选，指定用户名映射 JSON 文件路径，若不提供则使用数据库中的昵称。
- `--top-n <数字>`：可选，指定条形图中显示的用户对数，默认为 20（最多显示 20 对）。
- `--font <字体名称>`：可选，指定中文字体（例如 "Microsoft YaHei" 或 "SimHei"），用于图表显示。

### 使用示例

#### 分析整个群聊的数据（例如群号 98765432）
```vbnet
python main.py --group 98765432 --db nt_msg.clean.db --mode group --id 98765432 --font "Microsoft YaHei"
```
#### 分析特定用户（如 QQ 号 12345678）与他人的互动数据
```bash
python main.py --group 98765432 --db nt_msg.clean.db --focus-user 12345678 --mode group --id 98765432 --font "Microsoft YaHei"
```
#### 私聊模式使用示例
假如要分析与好友 QQ 号 87654321 的私聊数据：
```vbnet
python main.py --group 98765432 --db nt_msg.clean.db --mode c2c --id 87654321 --font "Microsoft YaHei"
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
- 作者技术水平，时间，精力有限，可能不能做到经常维护，敬请谅解，有什么建议/反馈可以提issue，但是不保证什么时候能解决就是了（）

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
