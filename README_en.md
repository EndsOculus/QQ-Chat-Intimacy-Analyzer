# QQ Group Chat Intimacy Analyzer

This project provides a tool for analyzing the intimacy (interaction closeness) between users in QQ group chats.  
The tool extracts chat records from an unencrypted SQLite database, cleans and normalizes the data, computes interaction metrics for each pair of users, and then calculates a comprehensive intimacy score based on preset weights. Finally, the tool outputs the results as a CSV file and generates visualizations—including a radar chart, a bar chart, and a comparison chart—to intuitively display the interaction dynamics among users.

## Features

- **Data Extraction and Cleaning**  
  - Extract group chat data from a SQLite database (supports both group chats and private chats).  
  - Automatically exclude system messages (e.g., users with QQ numbers 10000 and 2854196310).  
  - Extract both group nickname and QQ name; by default, the group nickname is used; if it is empty, the QQ name is used instead.  
  - Clean special Unicode characters, emojis, and Hangul fillers to ensure proper display of both Chinese and English characters and numbers.

- **Interaction Metrics Calculation**  
  - Compute metrics such as average response time, chat frequency (messages per day), interaction continuity (average consecutive rounds), reciprocity (balance in message counts), message length, reply count, and dialogue continuity (percentage of replies within 60 seconds).  
  - Supports custom weights with default settings:  
    - Average Response Time: 20%  
    - Chat Frequency: 20%  
    - Interaction Continuity: 15%  
    - Reciprocity: 10%  
    - Message Length: 10%  
    - Reply Count: 20%  
    - Dialogue Continuity: 5%  
  - Introduces an overall activity penalty factor for low-activity groups to ensure the final score reflects the actual interaction level.

- **Multiprocess Acceleration**  
  - Utilizes Python’s built-in multiprocessing module to accelerate the computation of interaction metrics between user pairs.  
  - Optimized for Python 3.13.

- **Visualization**  
  - Generates a radar chart displaying the normalized distribution of metrics.  
  - Generates a bar chart showing the top 20 user pairs with the highest intimacy scores. The bar chart automatically adjusts its vertical size to accommodate the labels.  
  - Generates a comparison chart to visually compare key metrics (average response time, average message length, reply count) for the user pair with the highest score.  
  - User names are formatted uniformly as “Name\<QQ#\>” (with email parts automatically removed). If a name is too long, a smaller font size is used in the legend to accommodate the full name.

- **Time Range Filtering**  
  - Interactive prompt for specifying a start and end date in the format `YYYY/MM/DD`.  
  - If no date is entered, the tool analyzes all available data.  
  - If only a start date is entered, the analysis is performed from that date onward; if only an end date is entered, analysis is done up to that date.

## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/QQ-Chat-Intimacy-Analyzer.git
cd QQ-Chat-Intimacy-Analyzer
```

### Install Dependencies

This project requires Python 3.13 and the following packages:  
- pandas  
- numpy  
- matplotlib  

Install the dependencies using pip:

```bash
pip install pandas numpy matplotlib
```

## Usage

### Data Preparation
- Ensure your database file (e.g., `nt_msg.clean.db`) is an unencrypted SQLite database and contains a table named `group_msg_table` with the following fields:
  - `"40027"`: Group chat number  
  - `"40033"`: Sender QQ number  
  - `"40090"`: Group nickname  
  - `"40093"`: QQ name  
  - `"40050"`: Sending time (Unix timestamp in seconds)  
  - `"40080"`: Message content  
  - `"40011"` and `"40012"` are used to determine the message type (only normal text messages are extracted).
- For decryption details (if needed), refer to [this resource](https://github.com/QQBackup/qq-win-db-key/issues/50).
- Optionally, create a `user_names.json` file to define custom display names:
  ```json
  {
    "12345678": "Reimu",
    "10101010": "Marisa"
  }
  ```

### Running Examples

#### Analyze the Entire Group Chat (e.g., group 98765432)
```bash
python main.py --group 98765432 --db nt_msg.clean.db --mode group --id 98765432 --font "Microsoft YaHei"
```

#### Analyze the Interaction Data for a Specific User (e.g., QQ number 12345678)
```bash
python main.py --group 98765432 --db nt_msg.clean.db --focus-user 12345678 --mode group --id 98765432 --font "Microsoft YaHei"
```

#### Interactive Time Range Filtering
After running the command, the program will prompt you to enter a start and end date:
- If you enter `2024/01/01` and then `2024/12/31`, only data from 2024 will be analyzed.
- Pressing Enter without input will analyze all data.
- Entering only a start date means analysis from that date onward; entering only an end date means analysis up to that date.

### Output Results
- **CSV File**: e.g., `intimacy_114514191.csv`, containing the interaction metrics and comprehensive intimacy scores for each user pair.
- **Chart Files**:
  - `radar_chart_multi.png`: Radar chart.
  - `bar_chart.png`: Bar chart.
  - `comparison_chart.png`: Comparison chart.

## Project Structure

```
QQ-Chat-Intimacy-Analyzer/
├── extract_chat_data.py        # Data extraction module
├── clean_chat_data.py          # Data cleaning module
├── intimacy_analysis.py        # Interaction metrics calculation and intimacy score module
├── visualization.py            # Visualization module
├── main.py                     # Entry point, integrating all modules
├── user_names.json             # User name mapping file (optional)
└── README.md                   # This document
```

## Notes

- Ensure that the database’s table structure and field names match those used in the SQL queries. Adjust the queries if necessary.
- For low-activity groups (e.g., class groups), an overall activity penalty factor is applied so that even if most normalized metrics are high, the final score remains low to reflect the low interaction level.
- The project utilizes multiprocessing for accelerated computation. It is recommended to run on machines with multiple CPU cores.
- For proper display of Chinese characters in the charts, please ensure your system has the appropriate Chinese fonts installed (e.g., Microsoft YaHei).

## License

MIT License

## Author

Created by [EndsOculus]

## Acknowledgements

- [pandas](https://pandas.pydata.org/)
- [numpy](https://numpy.org/)
- [matplotlib](https://matplotlib.org/)
- [Python](https://www.python.org/)
- [@F1](https://github.com/F1Justin)
- [qq-win-db-key](https://github.com/QQBackup/qq-win-db-key)
```