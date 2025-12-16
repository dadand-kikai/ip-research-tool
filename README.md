# IP Demand Research Tool

A Python-based tool to identify "upcoming IPs" for overseas sales using data from AniList and Reddit.

## Setup

1.  **Install Python**: Ensure Python 3.10+ is installed.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    (On Windows, you might need `py -m pip install -r requirements.txt`)

3.  **Configure Secrets**:
    - Copy `.env.example` to `.env`.
    - Fill in Reddit API credentials:
        - `REDDIT_CLIENT_ID`
        - `REDDIT_CLIENT_SECRET`
    - (If you don't have Reddit keys, the tool will run with AniList data only)

## Usage

Run the weekly batch:

```bash
python main.py
```
(Or `py main.py`)

## Output

- **`report.csv`**: Contains the ranked list of IPs with scores and SKU recommendations.
- **`ip_research.log`**: Execution logs.

## Troubleshooting

- **"Python was not found"**: Try using `py` instead of `python`.
- **"Reddit credentials missing"**: Check your `.env` file. You can still run the tool, but Reddit scores will be 0.
