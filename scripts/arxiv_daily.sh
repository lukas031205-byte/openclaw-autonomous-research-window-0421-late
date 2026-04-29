#!/bin/bash
# Daily arXiv paper fetcher for KAS

# Topics to search
TOPICS=("visual foundation model" "autonomous driving" "3D reconstruction" "lidar reconstruction" "radar reconstruction" "agentic memory" "large language model")

# Randomly pick a topic (seed with date for consistency each day)
DAY_OF_YEAR=$(date +%j)
TOPIC_INDEX=$((DAY_OF_YEAR % ${#TOPICS[@]}))
TOPIC="${TOPICS[$TOPIC_INDEX]}"

# File to track sent papers
TRACK_FILE="$HOME/.openclaw/workspace-domain/memory/arxiv/sent_papers.txt"
LOG_FILE="$HOME/.openclaw/workspace-domain/memory/arxiv/log.txt"

echo "$(date): Searching for: $TOPIC" >> "$LOG_FILE"

# Search arXiv via API (atom feed)
ARXIV_URL="http://export.arxiv.org/api/query?search_query=all:$TOPIC+AND+submittedDate:[$(date -d '1 day ago' +%Y%m%d)%20TO%20$(date +%Y%m%d)]&sortBy=submittedDate&sortOrder=descending&max_results=5"

RESPONSE=$(curl -s "$ARXIV_URL")

# Extract entries
PAPERS=$(echo "$RESPONSE" | grep -oP '(?<=<entry>).*?(?=</entry>)' | head -1)

if [ -z "$PAPERS" ]; then
    echo "$(date): No papers found for $TOPIC" >> "$LOG_FILE"
    exit 0
fi

# Extract details
TITLE=$(echo "$PAPERS" | grep -oP '(?<=<title>)[^<]+' | tr '\n' ' ')
SUMMARY=$(echo "$PAPERS" | grep -oP '(?<=<summary>)[^<]+' | head -1)
URL=$(echo "$PAPERS" | grep -oP '(?<=<id>)[^<]+')
AUTHORS=$(echo "$PAPERS" | grep -oP '(?<=<author><name>)[^<]+' | head -5 | tr '\n' ',')

# Check if already sent
if grep -q "$URL" "$TRACK_FILE" 2>/dev/null; then
    echo "$(date): Already sent $URL" >> "$LOG_FILE"
    exit 0
fi

# Format message
MESSAGE="📄 **今日 arXiv 论文 ($TOPIC)**

**标题:** $TITLE

**作者:** $AUTHORS

**摘要:**
$SUMMARY

🔗 [arXiv 链接]($URL)"

# Send via OpenClaw message
echo "$MESSAGE" > /tmp/arxiv_paper_msg.txt
echo "$URL" >> "$TRACK_FILE"

# Use OpenClaw to send - write to a temp file and trigger
echo "$(date): Found paper: $TITLE" >> "$LOG_FILE"

# Print the message for the cron to pick up
echo "ARXIV_TOPIC=$TOPIC"
echo "ARXIV_TITLE=$TITLE"
echo "ARXIV_URL=$URL"
echo "ARXIV_AUTHORS=$AUTHORS"
echo "ARXIV_SUMMARY=$SUMMARY"
