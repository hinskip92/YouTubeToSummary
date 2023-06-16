import openai
from openai import Audio
import os
import yt_dlp as youtube_dl
import guidance
from moviepy.editor import AudioFileClip
import streamlit as st
import os

output_dir = "C:/Users/Henry/Documents/GitHub/YTTranscriber/Chunks"
output_file = "video_audio.mp3"
chunk_length = 120 * 15
transcripts = []
folder_path = "C:/Users/Henry/Documents/GitHub/YTTranscriber/Chunks"
audio_file_path = "C:/Users/Henry/Documents/GitHub//YTTranscriber/.DownloadedAudio"
summary_llm = guidance.llms.OpenAI('gpt-3.5-turbo-16k-0613', caching=False)

st.set_page_config(
    page_title='YouTube Video to Summary',
    page_icon='🐾',
    initial_sidebar_state="auto",
    layout="wide"
)

st.markdown("<h1 style='text-align: center; color: white;'>YouTube Video to Summary</h1>", unsafe_allow_html=True)

st.sidebar.subheader("Enter Your API Key 🗝️")
open_api_key = st.sidebar.text_input(
    "Open API Key", 
    value=st.session_state.get('open_api_key', ''),
    help="Get your API key from https://openai.com/",
    type='password'
)
#os.environ["OPENAI_API_KEY"] = open_api_key
st.session_state['open_api_key'] = open_api_key
#load_dotenv(find_dotenv())

#Function to download the audio from a youtube video
def download_audio(url, output_file):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '.DownloadedAudio/' + output_file,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }],
        'ffmpeg_location': "C:/ffmpeg/bin"
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print("Download Complete")



# Function to split the audio file into smaller chunks
def split_audio_file(audio_file_path, chunk_length, output_dir):
    print("== Splitting audio...")
    audio = AudioFileClip(audio_file_path)
    duration = audio.duration
    chunks = []

    start_time = 0
    while start_time < duration:
        end_time = min(start_time + chunk_length, duration)
        chunk = audio.subclip(start_time, end_time)
        chunk_file = os.path.join(output_dir, f"chunk_{start_time}-{end_time}.mp3")
        chunk.write_audiofile(chunk_file)
        chunks.append(chunk_file)
        start_time += chunk_length

    return chunks

def transcribe_audio(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    print(transcript['text'])
    return transcript['text']

def transcribe_audio_dir(output_dir):
    global transcripts
    for filename in os.listdir(output_dir):
        if filename.endswith(".mp3"):
            file_path = os.path.join(output_dir, filename)
            transcript = transcribe_audio(file_path)
            summary = generate_summary(transcript)
            transcripts.append(summary)
            os.remove(file_path)
    print("Chunk Transcription and Summarization Complete")
    print(transcripts)

    #Summarize the transcripts using the LLM and write to a file

    output_path = os.path.join(os.getcwd(), "Transcripts", "summary.txt")
    with open(output_path, "w", encoding="utf-8") as file:
        for transcript in transcripts:
            file.write(transcript + "\n")

    return transcripts

def generate_summary(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=[
        {"role": "system", "content": "You are a world bestsummarizer. Condense the transcript text, capturing essential points and core points. Include relevant examples, omit excess details, and ensure the summary's length matches the original's complexity."},
        {"role": "user", "content": f"Please summarize the following text:\n{text}\nSummary:"},
    ],
        max_tokens=11000,
        stop=None,
        temperature=0.2,
    )
    summary = response['choices'][0]['message']['content'].strip()
    return summary

#download_audio(url, output_file)

import gradio as gr


def main():
    source = st.radio("Select audio source", ["YouTube Video", "Audio File"])
    if source == "YouTube Video":
        url = st.text_input(label="Video URL")
        audio_file = None
    else:  # Audio File
        audio_file = st.file_uploader("Upload audio file", type=["mp3", "wav"])
        url = None

    chunk_length = st.number_input(label="Chunk Length (seconds)", value=900, step=1)

    return url, "default_output", chunk_length, audio_file

def download_and_split_video(url, output_file, chunk_length, transcripts):
    download_audio(url, output_file)
    audio_file_path = '.DownloadedAudio/' + f"{output_file}.mp3"
    split_audio_file(audio_file_path, chunk_length, output_dir)
    os.remove(audio_file_path)
    return transcribe_audio_dir(output_dir)
    #return transcribe_audio_dir(transcripts)


if __name__ == "__main__":
    url, output_file, chunk_length, audio_file = main()  # get the values here

    if open_api_key:  # Check if API key is provided
        if st.button("Generate Summary"):
            with st.spinner("Summary Generating..."):
                if url:  # If YouTube URL is provided
                    transcripts = download_and_split_video(url, output_file, chunk_length, transcripts)
                elif audio_file:  # If an audio file is uploaded
                    audio_file_path = os.path.join('.DownloadedAudio/', output_file)
                    with open(audio_file_path, "wb") as f:
                        f.write(audio_file.getvalue())  # Write the content of the uploaded file to a new file
                    split_audio_file(audio_file_path, chunk_length, output_dir)
                    transcripts = transcribe_audio_dir(output_dir)
                    os.remove(audio_file_path)  # Delete saved audio file
                st.subheader("Summary")
                st.write(transcripts[0])
    else:  # If API key is not provided
        st.warning("Please Enter OpenAI API Key")  # Display warning message