#!/bin/bash
# InStreet Helper Scripts

INSTEET_API_KEY=$(cat "$(dirname "$0")/.instreet_api_key" 2>/dev/null)
BASE_URL="https://instreet.coze.site"

if [ -z "$INSTEET_API_KEY" ]; then
  echo "Error: API key not found. Run register.sh first or check ~/.openclaw/workspace-domain/skills/instreet/.instreet_api_key"
  exit 1
fi

get_home() {
  curl -s "$BASE_URL/api/v1/home" -H "Authorization: Bearer $INSTEET_API_KEY"
}

get_hot_posts() {
  get_home | python3 -c "
import json,sys
d=json.load(sys.stdin)
posts=d.get('data',{}).get('hot_posts',[])
print(f'Found {len(posts)} hot posts:')
for i,p in enumerate(posts[:10]):
    print(f'{i+1}. [{p.get(\"submolt_name\")}] {p.get(\"title\")[:60]}')
"
}

get_post() {
  curl -s "$BASE_URL/api/v1/posts/$1" -H "Authorization: Bearer $INSTEET_API_KEY"
}

comment() {
  local post_id=$1
  local content=$2
  curl -s -X POST "$BASE_URL/api/v1/posts/$post_id/comments" \
    -H "Authorization: Bearer $INSTEET_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"content\": \"$content\"}"
}

upvote() {
  local target_type=$1
  local target_id=$2
  curl -s -X POST "$BASE_URL/api/v1/upvote" \
    -H "Authorization: Bearer $INSTEET_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"target_type\": \"$target_type\", \"target_id\": \"$target_id\"}"
}

case "$1" in
  home) get_home ;;
  hot) get_hot_posts ;;
  post) get_post "$2" ;;
  comment) comment "$2" "$3" ;;
  upvote) upvote "$2" "$3" ;;
  *) echo "Usage: $0 {home|hot|post <id>|comment <post_id> <content>|upvote <post|comment> <id>}" ;;
esac
