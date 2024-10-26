import traceback
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
from typing import List, Type
import requests
from crewai_tools.tools.base_tool import BaseTool
from pydantic.v1 import BaseModel, Field
from groq import Groq
import openai
import time
import streamlit as st

YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

class FetchRelevantVideosFromYouTubeChannelInput(BaseModel):
    """Input for FetchRelevantVideosFromYouTubeChannel."""
    youtube_channel_handle: str = Field(
        ..., description="The YouTube channel handle (e.g., '@channelhandle')."
    )

class VideoInfo(BaseModel):
    video_id: str
    title: str
    description: str
    publish_date: datetime
    video_url: str
    category_id: str
    view_count: int
    like_count: int
    relevance_score: float = 0.0

class FetchRelevantVideosFromYouTubeChannelOutput(BaseModel):
    videos: List[VideoInfo]

class FetchRelevantVideosFromYouTubeChannelTool(BaseTool):
    name: str = "Fetch Relevant Videos for Channel"
    description: str = (
        "Fetches up to 200 latest videos for a specified YouTube channel handle, "
        "ranks them based on popularity and relevance to the creator's personal story, "
        "and returns the top 10 results, excluding short videos."
    )
    args_schema: Type[BaseModel] = FetchRelevantVideosFromYouTubeChannelInput
    return_schema: Type[BaseModel] = FetchRelevantVideosFromYouTubeChannelOutput

    def _run(
        self,
        youtube_channel_handle: str,
    ) -> FetchRelevantVideosFromYouTubeChannelOutput:
        api_key = YOUTUBE_API_KEY
        # api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable is not set")

        channel_id = self.get_channel_id(youtube_channel_handle, api_key)
        all_videos = self.fetch_all_videos(channel_id, api_key)
        video_details = self.fetch_video_details(all_videos, api_key)

        videos = []
        for video_id, details in video_details.items():
            snippet = details.get("snippet", {})
            statistics = details.get("statistics", {})

            if self.is_short_video(snippet):
                continue

            videos.append(
                VideoInfo(
                    video_id=video_id,
                    title=snippet.get("title", ""),
                    description=snippet.get("description", ""),
                    publish_date=datetime.fromisoformat(
                        snippet.get("publishedAt", "").replace("Z", "+00:00")
                    ).astimezone(timezone.utc),
                    video_url=f"https://www.youtube.com/watch?v={video_id}",
                    category_id=snippet.get("categoryId", ""),
                    view_count=int(statistics.get("viewCount", 0)),
                    like_count=int(statistics.get("likeCount", 0))
                )
            )

        # Sort by popularity (view count) and take top 50
        popular_videos = sorted(videos, key=lambda v: v.view_count, reverse=True)[:50]

        ranked_videos = self.rank_videos(popular_videos)
        # return FetchRelevantVideosFromYouTubeChannelOutput(videos=ranked_videos[:10])
        return FetchRelevantVideosFromYouTubeChannelOutput(videos=ranked_videos[:10])


    def get_channel_id(self, youtube_channel_handle: str, api_key: str) -> str:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "type": "channel",
            "q": youtube_channel_handle,
            "key": api_key,
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            items = response.json().get("items", [])
            if not items:
                raise ValueError(f"No channel found for handle {youtube_channel_handle}")
            return items[0]["id"]["channelId"]
        except requests.exceptions.RequestException as e:
            print(f"Error in get_channel_id: {e}")
            print(f"Response content: {response.content}")
            raise

    def is_short_video(self, snippet: dict) -> bool:
        title = snippet.get("title", "").lower()
        description = snippet.get("description", "").lower()
        return "#shorts" in title or "#shorts" in description or snippet.get("categoryId") == "22"

    def fetch_all_videos(self, channel_id: str, api_key: str) -> List[str]:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "id",
            "channelId": channel_id,
            "maxResults": 50,  # Maximum allowed per request
            "order": "date",
            "type": "video",
            "key": api_key,
        }

        all_video_ids = []
        page_token = None
        try:
            while len(all_video_ids) < 200:
                if page_token:
                    params["pageToken"] = page_token

                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                new_video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
                all_video_ids.extend(new_video_ids)

                page_token = data.get("nextPageToken")
                if not page_token or len(new_video_ids) == 0:
                    break  # No more pages or no new videos

                # Respect YouTube API quota limits
                time.sleep(1)  # Wait 1 second between requests

            return all_video_ids[:200]  # Ensure we don't exceed 200 videos
        except requests.exceptions.RequestException as e:
            print(f"Error in fetch_all_videos: {e}")
            print(f"Response content: {response.content}")
            raise

    def fetch_video_details(self, video_ids: List[str], api_key: str, batch_size: int = 50) -> dict:
        video_details = {}
        url = "https://www.googleapis.com/youtube/v3/videos"

        for i in range(0, len(video_ids), batch_size):
            batch = video_ids[i:i + batch_size]
            params = {
                "part": "snippet,statistics",
                "id": ",".join(batch),
                "key": api_key,
            }
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                batch_details = {item["id"]: item for item in response.json()["items"]}
                video_details.update(batch_details)

                # Respect YouTube API quota limits
                time.sleep(1)  # Wait 1 second between requests
            except requests.exceptions.RequestException as e:
                print(f"Error in fetch_video_details: {e}")
                print(f"Response content: {response.content}")
                raise

        return video_details

    def rank_videos(self, videos: List[VideoInfo]) -> List[VideoInfo]:
        # groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        groq_client = GROQ_API_KEY
        
        for video in videos:
            prompt = f"""
            Rate how likely this video is to cover the personal story of its creator. Respond with a single number from 0 to 10, where 0 means not at all likely and 10 means extremely likely.

            Title: {video.title}
            Description: {video.description}

            Rating (0-10):
            """

            try:
                response = groq_client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an AI that rates videos based on their relevance to the creator's personal story. Respond only with a number from 0 to 10."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=5,
                    temperature=0.2
                )

                score_text = response.choices[0].message.content.strip()
                try:
                    score = float(score_text)
                    if 0 <= score <= 10:
                        video.relevance_score = score * 10  # Convert to 0-100 scale
                    else:
                        raise ValueError(f"Score out of range: {score}")
                except ValueError:
                    print(f"Failed to parse score for video {video.title}: {score_text}")
                    video.relevance_score = 0
            except Exception as e:
                print(f"Error with Groq API for video {video.title}: {str(e)}")
                video.relevance_score = 0

        return sorted(videos, key=lambda v: v.relevance_score, reverse=True)