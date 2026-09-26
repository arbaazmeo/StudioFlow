import os
import re
import time
import json
import isodate
import requests
from datetime import datetime, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

API_KEY = os.getenv("YOUTUBE_API_KEY")

def execute_with_retry(request, max_retries=5):
    for attempt in range(max_retries):
        try:
            return request.execute()
        except HttpError as e:
            if e.resp.status in [403, 429, 500, 503]:
                time.sleep((2 ** attempt) + 1)
            else:
                raise e
    raise TimeoutError("Max API retries exceeded.")

def get_youtube_client():
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise ValueError("YOUTUBE_API_KEY environment variable is not set.")
    return build('youtube', 'v3', developerKey=key)

def get_channel_details(youtube, channel_input):
    clean_input = channel_input.strip()
    
    if clean_input.startswith("@"):
        req = youtube.channels().list(part="snippet,contentDetails,statistics", forHandle=clean_input)
        res = execute_with_retry(req)
    else:
        req = youtube.channels().list(part="snippet,contentDetails,statistics", id=clean_input)
        res = execute_with_retry(req)

    if not res.get('items'):
        search_req = youtube.search().list(part="snippet", q=clean_input, type="channel", maxResults=1)
        search_res = execute_with_retry(search_req)
        if not search_res.get('items'):
            raise ValueError(f"Channel '{channel_input}' could not be resolved.")
        channel_id = search_res['items'][0]['snippet']['channelId']
        req = youtube.channels().list(part="snippet,contentDetails,statistics", id=channel_id)
        res = execute_with_retry(req)

    item = res['items'][0]
    return {
        "id": item['id'],
        "title": item['snippet']['title'],
        "description": item['snippet']['description'],
        "created_at": item['snippet']['publishedAt'],
        "subscribers": int(item['statistics'].get('subscriberCount', 0)),
        "video_count": int(item['statistics'].get('videoCount', 0)),
        "uploads_playlist_id": item['contentDetails']['relatedPlaylists']['uploads']
    }

def get_all_playlist_video_ids(youtube, playlist_id):
    video_ids = []
    next_page_token = None

    while True:
        req = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        res = execute_with_retry(req)
        for item in res.get('items', []):
            video_ids.append(item['contentDetails']['videoId'])
            
        next_page_token = res.get('nextPageToken')
        if not next_page_token:
            break

    return video_ids

def fetch_video_details_batch(youtube, video_ids, channel_subscribers):
    videos = []
    now = datetime.now(timezone.utc)

    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        req = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(chunk)
        )
        res = execute_with_retry(req)

        for item in res.get('items', []):
            try:
                v_id = item['id']
                snippet = item.get('snippet', {})
                stats = item.get('statistics', {})
                cd = item.get('contentDetails', {})

                duration_sec = int(isodate.parse_duration(cd.get('duration', 'PT0S')).total_seconds())
                pub_date = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
                days_published = max((now - pub_date).days, 1)

                views = int(stats['viewCount']) if stats.get('viewCount') is not None else 0
                likes = int(stats['likeCount']) if stats.get('likeCount') is not None else 0
                comments = int(stats['commentCount']) if stats.get('commentCount') is not None else 0

                view_velocity = views / days_published
                views_per_sub = views / max(channel_subscribers, 1)
                engagement_rate = (likes + comments) / max(views, 1)
                is_short = duration_sec <= 60

                videos.append({
                    "id": v_id,
                    "title": snippet.get('title', ''),
                    "description": snippet.get('description', ''),
                    "published_at": snippet.get('publishedAt', ''),
                    "tags": snippet.get('tags', []),
                    "thumbnail_url": snippet.get('thumbnails', {}).get('high', {}).get('url'),
                    "duration_sec": duration_sec,
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "metrics": {
                        "view_velocity": view_velocity,
                        "views_per_subscriber": views_per_sub,
                        "engagement_rate": engagement_rate,
                        "is_short": is_short
                    }
                })
            except Exception as e:
                print(f"Skipping video {item.get('id')} due to processing error: {e}")

    return videos

def flag_outliers(videos):
    if not videos:
        return videos
    
    velocities = sorted([v['metrics']['view_velocity'] for v in videos])
    mid = len(velocities) // 2
    median_velocity = velocities[mid] if len(velocities) % 2 != 0 else (velocities[mid-1] + velocities[mid]) / 2

    for v in videos:
        v['is_outlier'] = v['metrics']['view_velocity'] > (1.5 * median_velocity)

    return videos

def get_video_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_90s = " ".join([t['text'] for t in transcript_list if t['start'] <= 90])
        return transcript_90s
    except (TranscriptsDisabled, NoTranscriptFound, Exception):
        return None

def get_top_comments(youtube, video_id, max_results=20):
    try:
        req = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            order="relevance",
            maxResults=max_results
        )
        res = execute_with_retry(req)
        return [item['snippet']['topLevelComment']['snippet']['textDisplay'] for item in res.get('items', [])]
    except Exception:
        return []

def compute_summary_analytics(videos):
    if not videos:
        return {}

    dates = [datetime.fromisoformat(v['published_at'].replace('Z', '+00:00')) for v in videos]
    dates.sort()

    day_counts = {day: 0 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
    for d in dates:
        day_counts[d.strftime("%A")] += 1

    days_diffs = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
    avg_days_between_uploads = sum(days_diffs) / max(len(days_diffs), 1)

    question_titles = 0
    title_words_count = []
    first_words = {}
    titles_with_numbers = 0

    for v in videos:
        title = v['title']
        words = title.split()
        title_words_count.append(len(words))

        if "?" in title:
            question_titles += 1
        if re.search(r'\d', title):
            titles_with_numbers += 1
        if words:
            fw = words[0].strip().capitalize()
            first_words[fw] = first_words.get(fw, 0) + 1

    return {
        "upload_cadence": {
            "day_of_week_distribution": day_counts,
            "avg_days_between_uploads": round(avg_days_between_uploads, 2)
        },
        "title_patterns": {
            "question_vs_statement_ratio": f"{question_titles}:{len(videos) - question_titles}",
            "titles_with_numbers_count": titles_with_numbers,
            "avg_word_count": round(sum(title_words_count) / max(len(videos), 1), 2),
            "common_first_words": dict(sorted(first_words.items(), key=lambda item: item[1], reverse=True)[:10])
        }
    }

def download_thumbnails(channel_id, videos):
    folder_path = os.path.join("thumbnails", channel_id)
    os.makedirs(folder_path, exist_ok=True)

    for v in videos:
        url = v.get('thumbnail_url')
        if url:
            img_path = os.path.join(folder_path, f"{v['id']}.jpg")
            if not os.path.exists(img_path):
                try:
                    res = requests.get(url, timeout=10)
                    if res.status_code == 200:
                        with open(img_path, 'wb') as f:
                            f.write(res.content)
                except Exception:
                    pass

def analyze_and_clone_channel(channel_input):
    youtube = get_youtube_client()
    channel_meta = get_channel_details(youtube, channel_input)
    channel_id = channel_meta['id']

    video_ids = get_all_playlist_video_ids(youtube, channel_meta['uploads_playlist_id'])
    videos = fetch_video_details_batch(youtube, video_ids, channel_meta['subscribers'])
    videos = flag_outliers(videos)

    outliers = sorted([v for v in videos if v.get('is_outlier')], key=lambda x: x['metrics']['view_velocity'], reverse=True)[:10]

    for v in outliers:
        v['transcript_90s'] = get_video_transcript(v['id'])
        v['top_comments'] = get_top_comments(youtube, v['id'])

    summary_analytics = compute_summary_analytics(videos)
    summary_analytics['top_outliers'] = [v['id'] for v in outliers]
    download_thumbnails(channel_id, videos)

    full_output = {
        "channel_metadata": channel_meta,
        "summary_analytics": summary_analytics,
        "videos": videos
    }

    os.makedirs("output", exist_ok=True)
    json_path = os.path.abspath(os.path.join("output", f"{channel_id}_full_analysis.json"))
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=4)

    return json_path, full_output

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python core/channel_cloner.py <@handle_or_channel_id>")
        sys.exit(1)

    target_channel = sys.argv[1]
    file_path, _ = analyze_and_clone_channel(target_channel)
    print(f"Analysis complete! Saved structured report to: {file_path}")