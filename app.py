import streamlit as st
import asyncio
import edge_tts
import assemblyai as aai
from google import genai
from google.genai import types
import subprocess
import os

st.set_page_config(page_title="Movie Recap AI Tool", page_icon="🎬", layout="centered")

st.title("🎬 Movie Recap Automation Tool")
st.write("ဗီဒီယို တင်လိုက်ရုံနဲ့ မြန်မာ AI အသံပါတဲ့ Movie Recap ဗီဒီယို ဖန်တီးပေးမယ့် Web App")

# API Keys Input Section
with st.sidebar:
    st.header("⚙️ API Keys ပြင်ဆင်ရန်")
    gemini_key = st.text_input("Gemini API Key", type="password")
    assemblyai_key = st.text_input("AssemblyAI API Key (Optional)", type="password")
    
    st.header("🎙️ AI အသံ ချိန်ညှိရန်")
    voice_option = st.selectbox("အသံ ရွေးရန်", ["my-MM-ThihaNeural (အမျိုးသား)", "my-MM-NilarNeural (အမျိုးသမီး)"])
    voice_name = voice_option.split(" ")[0]
    voice_rate = st.slider("အသံ မြန်နှုန်း (Speed)", -20, 30, 15, format="%d%%")

# Upload Video
uploaded_video = st.file_uploader("Recap လုပ်ချင်သည့် ဗီဒီယိုဖိုင် တင်ပါ (MP4)", type=["mp4", "mov", "avi"])

if st.button("🚀 1-Click Recap စတင်မည်"):
    if not gemini_key:
        st.error("Gemini API Key ကို ဘေးဘက် Sidebar မှာ အရင်ထည့်ပေးပါ။")
    elif uploaded_video is None:
        st.warning("ဗီဒီယိုဖိုင် အရင် Upload တင်ပေးပါ။")
    else:
        with st.spinner("Processing... ခဏစောင့်ပါ..."):
            # 1. Save uploaded file
            video_path = "input_video.mp4"
            with open(video_path, "wb") as f:
                f.write(uploaded_video.read())
            
            # 2. Transcription
            st.info("⚡ [1/3] ဗီဒီယိုမှ စကားပြောများကို စာသားပြောင်းနေသည်...")
            if assemblyai_key:
                aai.settings.api_key = assemblyai_key
                transcriber = aai.Transcriber()
                raw_text = transcriber.transcribe(video_path).text
            else:
                raw_text = "Video transcription processing"

            # 3. Gemini Script Generation
            st.info("⚡ [2/3] Gemini AI ဖြင့် မြန်မာ Script ရေးသားနေသည်...")
            client = genai.Client(api_key=gemini_key)
            prompt = f"""
            Below is the transcript of a video clip:
            "{raw_text}"
            
            You are an expert viral TikTok Movie Recap narrator.
            Task: Write a fast-paced, highly engaging Movie Recap script in Burmese language.
            Strict Rules: Start immediately with a dramatic hook line (No "Hello" / "ဒီနေ့မှာတော့"). Write in natural spoken Burmese narration. Output ONLY raw spoken text without scene notes/brackets.
            """
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=8192)
            )
            burmese_script = response.text.strip()
            
            st.text_area("📝 ထွက်လာသော မြန်မာ Script", burmese_script, height=150)
            
            # 4. Audio Generation & Video Merge
            st.info("⚡ [3/3] AI အသံသွင်းပြီး ဗီဒီယို ပေါင်းစပ်နေသည်...")
            rate_str = f"+{voice_rate}%" if voice_rate >= 0 else f"{voice_rate}%"
            
            async def make_audio():
                communicate = edge_tts.Communicate(burmese_script, voice_name, rate=rate_str)
                await communicate.save("recap_voice.mp3")
            asyncio.run(make_audio())
            
            output_video = "final_recap.mp4"
            cmd = f'ffmpeg -y -i "{video_path}" -i recap_voice.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest "{output_video}"'
            subprocess.run(cmd, shell=True)
            
            st.success("✅ ပြီးပါပြီ!")
            st.video(output_video)
            
            with open(output_video, "rb") as file:
                st.download_button(
                    label="⬇️ Final Video ဒေါင်းလုဒ်ဆွဲရန်",
                    data=file,
                    file_name="final_recap.mp4",
                    mime="video/mp4"
                )
