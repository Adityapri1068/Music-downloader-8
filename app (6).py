
import streamlit as st
import yt_dlp
from PIL import Image
import requests
from io import BytesIO
import os

st.set_page_config(page_title="🎧 Music & Video Downloader", page_icon="🎧")
st.title("🎧 Music & Video Downloader")
st.markdown("### 🔎 Search YouTube or Paste a Video/Playlist URL")

# Setup directory
download_dir = "downloads"
os.makedirs(download_dir, exist_ok=True)

# Initialize session state
for key in ["video_url", "video_info", "format_type", "selected_quality"]:
    if key not in st.session_state:
        st.session_state[key] = None

search_mode = st.radio("Select Mode", ["🔍 Keyword Search", "📎 Paste URL"])

# Input handling
if search_mode == "🔍 Keyword Search":
    keyword = st.text_input("Enter search term (e.g., lofi chill mix)")
    if st.button("🔍 Search"):
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                results = ydl.extract_info(f"ytsearch10:{keyword}", download=False)["entries"]
                for idx, entry in enumerate(results):
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.image(entry["thumbnail"], width=100)
                    with col2:
                        st.markdown(f"**{entry['title']}**")
                        if st.button("Download this", key=f"select_{idx}"):
                            st.session_state.video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            st.session_state.video_info = None
        except Exception:
            st.error("❌ Search failed. Try again.")

elif search_mode == "📎 Paste URL":
    url_input = st.text_input("Paste YouTube URL")
    if st.button("🔍"):
        st.session_state.video_url = url_input
        st.session_state.video_info = None

# Load video info only once
if st.session_state.video_url and st.session_state.video_info is None:
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(st.session_state.video_url, download=False)
            st.session_state.video_info = info
    except Exception:
        st.error("❌ Unable to load video/playlist.")
        st.stop()

info = st.session_state.video_info
url = st.session_state.video_url

# Playlist or single video
if info:
    if '_type' in info and info['_type'] == 'playlist':
        st.markdown(f"### 📃 Playlist: {info['title']} ({len(info['entries'])} videos)")
        for idx, entry in enumerate(info['entries']):
            st.markdown(f"**{idx+1}. {entry['title']}**")
            if st.button("Download", key=f"pl_dl_{idx}"):
                try:
                    ydl_opts = {
                        'format': '18',
                        'outtmpl': os.path.join(download_dir, f"{entry['title']}.mp4"),
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([entry['webpage_url']])
                    st.success("Downloaded successfully.")
                except Exception:
                    st.error("Download failed. Try again.")
    else:
        title = info.get("title")
        thumbnail_url = info.get("thumbnail")
        formats = info.get("formats", [])

        if thumbnail_url:
            response = requests.get(thumbnail_url)
            img = Image.open(BytesIO(response.content))
            st.image(img, caption="Thumbnail", use_column_width=True)

        format_choice = st.radio("Choose format", ["Audio (.webm)", "Video (.mp4)", "Thumbnail"])

        if format_choice == "Video (.mp4)":
            quality_options = []
            quality_map = {}
            for f in formats:
                if f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("ext") == "mp4":
                    label = f"{f['format_id']} - {f.get('height', 0)}p"
                    quality_options.append(label)
                    quality_map[label] = f["format_id"]
            selected_quality = st.selectbox("Select Quality", quality_options)
            st.session_state.selected_quality = quality_map[selected_quality]
        else:
            st.session_state.selected_quality = None

        if st.button("⬇ Download Now"):
            try:
                if format_choice == "Audio (.webm)":
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(download_dir, f"{title}.webm")
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    st.success("Audio downloaded successfully!")
                    st.audio(os.path.join(download_dir, f"{title}.webm"))

                elif format_choice == "Video (.mp4)":
                    ydl_opts = {
                        'format': st.session_state.selected_quality,
                        'outtmpl': os.path.join(download_dir, f"{title}.mp4")
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    st.success("Video downloaded successfully!")
                    st.video(os.path.join(download_dir, f"{title}.mp4"))

                elif format_choice == "Thumbnail":
                    image_path = os.path.join(download_dir, f"{title}_thumbnail.jpg")
                    img.save(image_path)
                    st.success("Thumbnail image saved!")
                    st.image(image_path, caption="Saved Thumbnail")
            except Exception:
                st.error("❌ Failed to download. Try another format or video.")
