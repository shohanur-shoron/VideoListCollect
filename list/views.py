from django.contrib.auth.models import User
from django.shortcuts import render
from django.shortcuts import redirect
from .models import YouTubeVideo
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.conf import settings
from django.db.models import Sum

from urllib.parse import urlparse, parse_qs

import isodate
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import time


def human_readable_duration(total_seconds):
    """Converts total_seconds into a format like '2h 34m 3s'."""
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"


def has_bangla_auto_transcript(video_url):
    """
    Checks if the video has a Bangla (auto-generated) transcript.
    Returns True if found, otherwise False.
    """

    # Extract the video_id from the URL
    video_id = extract_video_id(video_url)
    
    try:
        # List all transcript tracks for this video
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Check if any transcript is Bangla and auto-generated
        for transcript in transcript_list:
            if transcript.language_code == 'bn' and transcript.is_generated:
                return True
        
        # If we get here, there is no Bangla auto-generated transcript
        return False
    
    except Exception as e:
        # Handle exceptions (e.g., video not available, no transcripts at all, etc.)
        print(f"Error checking transcripts: {e}")
        return False


def format_duration(total_seconds: int) -> str:
    """
    Convert an integer number of seconds into a
    human-readable string: Hh Mm Ss (e.g. "2h 34m 3s").
    Handles hours, minutes, and seconds.
    """
    hours = total_seconds // 3600
    remainder = total_seconds % 3600
    minutes = remainder // 60
    seconds = remainder % 60

    parts = []
    if hours > 0:
        parts.append(f"{int(hours)}h")
    if minutes > 0:
        parts.append(f"{int(minutes)}m")
    if seconds > 0:
        parts.append(f"{int(seconds)}s")

    # If total_seconds = 0 (shouldn't happen if min is 1),
    # or if there's no hours/minutes, we still return something.
    if not parts:
        return "0s"

    return " ".join(parts)


def is_invalid(url: str) -> bool:
    """
    Checks if a YouTube link is invalid based on:
      - Overall link length constraints
      - Domain check (youtube.com, www.youtube.com, youtu.be)
      - Extractable and valid-length video ID
    Returns True if invalid, False if valid.
    """
    # 1. Quick check: length of the entire link
    #    (Adjust these bounds as you see fit.)
    if len(url) < 45 or len(url) > 64:
        return True

    # 2. Parse the domain
    try:
        parsed = urlparse(url)
    except Exception:
        return True  # Not a valid URL at all

    valid_domains = ['youtube.com', 'www.youtube.com', 'youtu.be']
    if parsed.hostname not in valid_domains:
        return True

    # 3. Try extracting the video ID and check length
    try:
        video_id = extract_video_id(url)
        # Typical YouTube IDs are often 11 characters, but can vary.
        # Adjust the range as needed:
        if len(video_id) != 11:
            return True
    except ValueError:
        # If we can't extract a video ID, it's invalid
        return True

    # If none of the above checks failed, it's valid
    return False


def extract_video_id(url: str) -> str:
    """
    Extracts the YouTube video ID from either a short youtu.be URL or a
    standard youtube.com/watch?v=... URL.
    Raises ValueError if extraction fails.
    """
    parsed_url = urlparse(url)

    # Handle short youtu.be URL (e.g., https://youtu.be/VIDEO_ID)
    if 'youtu.be' in parsed_url.netloc:
        # video ID is the path without the leading '/'
        video_id = parsed_url.path.lstrip('/')
    else:
        # Handle standard youtube.com/watch?v=VIDEO_ID
        query_params = parse_qs(parsed_url.query)
        video_id = query_params.get('v', [None])[0]

    if not video_id:
        raise ValueError("Invalid YouTube URL. Could not extract video ID.")

    return video_id


def get_channel_name_and_duration(url: str, api_key: str) -> tuple[str, float]:
    """
    Given a YouTube video URL and an API key, returns a tuple:
        (channel_name, duration_in_seconds)
    Raises ValueError if the video cannot be found or accessed.
    """
    video_id = extract_video_id(url)

    youtube = build('youtube', 'v3', developerKey=api_key)
    response = youtube.videos().list(
        part="snippet,contentDetails",
        id=video_id
    ).execute()

    items = response.get('items', [])
    if not items:
        raise ValueError(f"No video found or access denied for video ID: {video_id}")

    snippet = items[0]['snippet']
    content_details = items[0]['contentDetails']

    channel_name = snippet['channelTitle']
    duration_iso8601 = content_details['duration']
    duration_seconds = isodate.parse_duration(duration_iso8601).total_seconds()

    return channel_name, duration_seconds


def get_video_title(url: str, api_key: str) -> str:
    """
    Given a YouTube video URL and an API key, returns the video's title.
    """
    video_id = extract_video_id(url)

    # Initialize the YouTube Data API client
    youtube = build("youtube", "v3", developerKey=api_key)

    # Request the snippet part to get the title
    response = youtube.videos().list(
        part="snippet",
        id=video_id
    ).execute()

    items = response.get("items", [])
    if not items:
        raise ValueError(f"No video found or access denied for video ID: {video_id}")

    snippet = items[0]["snippet"]
    return snippet["title"]


def logOutUser(request):
    logout(request)
    return redirect('create_list')


def create_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        name = request.POST['name']
        password = request.POST['password']
        confirmPassword = request.POST['confirmPassword']
        
        if password != confirmPassword:
            messages.error(request, 'Password did not mached!')
            return redirect('create_user')
        
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.delete()
        
        user = User.objects.create_user(username=username, first_name=name, password=password)
        user.save()
        return redirect('login_user')
    return render(request, "signup.html")
        

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
                login(request, user)
                return redirect("create_list")
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('login_user')
    return render(request, 'login.html')    
    

def create_list(request):
    if request.method == 'POST':
        link = request.POST['link']
        
        if is_invalid(link):
            messages.info(request, 'Invalid Youtube video link. Enter a valid one.')
            return redirect('create_list')
        
        
        video_id = extract_video_id(link)
        
        if YouTubeVideo.objects.filter(video_id=video_id).exists():
            messages.info(request, 'This video already exists in the list')
            return redirect('create_list')
        
        channel, duration = get_channel_name_and_duration(link, settings.YOUTUBE_API_KEY)
        
        total_duration = (
            YouTubeVideo.objects
            .filter(channel_name=channel)
            .aggregate(Sum('duration_seconds'))['duration_seconds__sum']
            or 0
        )
        
        
        total = YouTubeVideo.objects.filter(channel_name=channel).count()
        
        time.sleep(0.5)
        
        time.sleep(0.5)
        
        video = YouTubeVideo.objects.create(
            url = link,
            video_id = video_id,
            channel_name = channel,
            title = get_video_title(link, settings.YOUTUBE_API_KEY),
            duration_seconds = duration,
            type = "Long",
            added_by = request.user if request.user.is_authenticated else None
        )
        messages.info(request, 'Link successfully added to the list')
        return redirect('create_list')
    return render(request, 'addLink.html')


def create_short_video_list(request):
    if request.method == 'POST':
        link = request.POST['link']
        
        if is_invalid(link):
            messages.info(request, 'Invalid Youtube video link. Enter a valid one.')
            return redirect('create_short_video_list')
        
        
        video_id = extract_video_id(link)
        
        if YouTubeVideo.objects.filter(video_id=video_id).exists():
            messages.info(request, 'This video already exists in the list')
            return redirect('create_short_video_list')
        
        channel, duration = get_channel_name_and_duration(link, settings.YOUTUBE_API_KEY)
        
        total_duration = (
            YouTubeVideo.objects
            .filter(channel_name=channel)
            .aggregate(Sum('duration_seconds'))['duration_seconds__sum']
            or 0
        )
        
        
        total = YouTubeVideo.objects.filter(channel_name=channel).count()
        
        time.sleep(0.5)
        
        video = YouTubeVideo.objects.create(
            url = link,
            video_id = video_id,
            channel_name = channel,
            title = get_video_title(link, settings.YOUTUBE_API_KEY),
            duration_seconds = duration,
            type = "Short",
            added_by = request.user if request.user.is_authenticated else None
        )
        
        total_duration = (
            YouTubeVideo.objects
            .filter(channel_name=channel)
            .aggregate(Sum('duration_seconds'))['duration_seconds__sum']
        )
        
        inHours = format_duration(total_duration)
        total = YouTubeVideo.objects.filter(channel_name=channel).count()
        messages.info(request, 'Link successfully added to the list')
        messages.info(request, f"The {channel} channel has total {total} videos")
        messages.info(request, f"with total duration {inHours}")
        return redirect('create_short_video_list')
    return render(request, 'addLinkShort.html')
        

def view_table(request):
    data = YouTubeVideo.objects.all()
    length = 0
    for video in data:
        length += video.duration_seconds
    context = {
        'data':data,
        'empty':True if len(data) == 0 else False,
        'total_length': format_duration(length)
    }
    return render(request, "view.html", context)
        
        
def video_list_by_date(request):
    videos = YouTubeVideo.objects.filter(type="Long").order_by('created_at')

    grouped_videos = {}
    for video in videos:
        video_date = video.created_at.date() 

        if video_date not in grouped_videos:
            grouped_videos[video_date] = []

        grouped_videos[video_date].append(video)

    context = {
        'grouped_videos': grouped_videos,
        'empty':True if len(grouped_videos) == 0 else False
    }
    return render(request, 'link.html', context)


def video_list_by_channel(request):
    videos = YouTubeVideo.objects.filter(type="Short").order_by('channel_name')

    grouped_videos = {}
    for video in videos:
        channel = video.channel_name

        # If we haven't seen this channel before, initialize
        if channel not in grouped_videos:
            grouped_videos[channel] = {
                'videos': [],
                'total_duration_seconds': 0,
            }

        # Append the video and add its duration to the channel total
        grouped_videos[channel]['videos'].append(video)
        grouped_videos[channel]['total_duration_seconds'] += video.duration_seconds

    # Convert total seconds to human-readable format for each channel
    for channel_data in grouped_videos.values():
        channel_data['total_duration_human'] = format_duration(
            int(channel_data['total_duration_seconds'])
        )

    context = {
        'grouped_videos': grouped_videos,
        'empty': True if len(grouped_videos) == 0 else False
    }
    return render(request, 'shortVideoLinks.html', context)