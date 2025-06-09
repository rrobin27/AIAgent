# === Streamlit App: CS AI Agent with YouTube + Gemini + PDF Upload ===
# pip install google-api-python-client streamlit PyPDF2 python-dotenv google-generativeai

import os
import streamlit as st
from googleapiclient.discovery import build
import PyPDF2
from dotenv import load_dotenv
import google.generativeai as genai

# === Load environment variables from .env if available ===
load_dotenv()

# === API Keys (must be stored in environment variables) ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not GEMINI_API_KEY or not YOUTUBE_API_KEY:
    raise ValueError("Missing API keys. Please set GEMINI_API_KEY and YOUTUBE_API_KEY as environment variables.")

# === Initialize Gemini client ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# === YouTube Search Function ===
def search_youtube(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        part="snippet",
        q=query,
        maxResults=3,
        type="video"
    )
    response = request.execute()
    results = []
    for item in response["items"]:
        video_data = {
            "title": item["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        }
        results.append(video_data)
    return results

# === Gemini Streaming Function ===
def ask_gemini_streaming(prompt):
    response = model.generate_content(prompt, stream=True)
    output = ""
    for chunk in response:
        if chunk.text:
            output += chunk.text
            yield chunk.text
    yield "\n---\n\n✅ Complete."

# === Extract Text from PDF ===
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text[:5000]  # limit for input size safety

# === Streamlit UI ===
st.set_page_config(page_title="CS AI Agent", page_icon="🧠")
st.title("💡 Computer Science AI Assistant")

# === PDF Upload ===
st.sidebar.header("📄 Upload Notes or Textbook (PDF)")
pdf_file = st.sidebar.file_uploader("Upload PDF for custom Q&A", type=["pdf"])

custom_context = ""
if pdf_file is not None:
    custom_context = extract_text_from_pdf(pdf_file)
    st.sidebar.success("PDF loaded. Ask something based on it!")

query = st.text_input("Ask a computer science question or request a video:", "Explain Dijkstra's algorithm")

if st.button("Search"):
    with st.spinner("Thinking..."):
        if "video" in query.lower():
            videos = search_youtube(query)
            st.subheader("🎬 Top YouTube Videos")
            for video in videos:
                st.markdown(f"[{video['title']}]({video['url']})")
        else:
            full_prompt = f"{custom_context}\n\nQuestion: {query}" if custom_context else f"Explain this computer science concept clearly: {query}"
            st.subheader("📘 Explanation")
            response_placeholder = st.empty()
            streamed_output = ""
            for chunk in ask_gemini_streaming(full_prompt):
                streamed_output += chunk
                response_placeholder.markdown(streamed_output)

st.markdown("---")
st.caption("Created with ❤️ using Streamlit, Gemini, and YouTube API")
