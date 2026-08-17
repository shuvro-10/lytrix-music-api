from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
import yt_dlp

app = FastAPI(title="Lytrix API")
ytmusic = YTMusic()

# ক্রস-অরিজিন এলাউ করার জন্য
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Active", "message": "Welcome to Lytrix Music API"}

@app.get("/search")
def search_music(q: str):
    try:
        # ytmusicapi দিয়ে শুধু গান সার্চ করবে
        results = ytmusic.search(query=q, filter="songs", limit=20)
        formatted_results = []
        
        for item in results:
            # হাই-কোয়ালিটি থাম্বনেইল নেওয়ার চেষ্টা
            thumbnails = item.get("thumbnails", [])
            thumbnail_url = thumbnails[-1].get("url") if thumbnails else ""
            
            # আর্টিস্টের নামগুলো একসাথে করা
            artists = ", ".join([a["name"] for a in item.get("artists", [])])
            
            formatted_results.append({
                "videoId": item.get("videoId"),
                "title": item.get("title"),
                "artist": artists,
                "thumbnailUrl": thumbnail_url,
                "duration": item.get("duration")
            })
            
        return {"data": formatted_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream")
def get_stream(video_id: str):
    try:
        # yt-dlp দিয়ে ডাইরেক্ট অডিও লিংক বের করা
        ydl_opts = {
            'format': 'm4a/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            url = None
            
            # এক্সো-প্লেয়ারের জন্য m4a/mp4 ফরম্যাট ফিল্টার করা
            for f in info.get('formats', []):
                if f.get('ext') == 'm4a' and f.get('acodec') != 'none':
                    url = f.get('url')
                    break
            
            # যদি m4a না পায়, তাহলে যেকোনো বেস্ট অডিও লিংক নেবে
            if not url:
                url = info.get('url')
                
        return {"streamUrl": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
