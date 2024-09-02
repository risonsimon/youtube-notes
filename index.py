#!/usr/bin/env python

import sys
import os
import subprocess
import pyperclip
from yt_dlp import YoutubeDL
from litellm import completion
import litellm
from dotenv import load_dotenv
import re
import markdown2
import pdfkit
from pathlib import Path
import unicodedata
import glob
import time
import argparse

load_dotenv()

def remove_tags(text):
    """
    Remove vtt markup tags
    """
    tags = [
        r'</c>',
        r'<c(\.color\w+)?>',
        r'<\d{2}:\d{2}:\d{2}\.\d{3}>',
    ]

    for pat in tags:
        text = re.sub(pat, '', text)

    # extract timestamp, only keep HH:MM
    text = re.sub(
        r'(\d{2}:\d{2}):\d{2}\.\d{3} --> .* align:start position:0%',
        r'\g<1>',
        text
    )

    text = re.sub(r'^\s+$', '', text, flags=re.MULTILINE)
    return text

def remove_header(lines):
    """
    Remove vtt file header
    """
    pos = -1
    for mark in ('##', 'Language: en',):
        if mark in lines:
            pos = lines.index(mark)
    lines = lines[pos+1:]
    return lines

def merge_duplicates(lines):
    """
    Remove duplicated subtitles. Duplicates are always adjacent.
    """
    last_timestamp = ''
    last_cap = ''
    for line in lines:
        if line == "":
            continue
        if re.match('^\d{2}:\d{2}$', line):
            if line != last_timestamp:
                yield line
                last_timestamp = line
        else:
            if line != last_cap:
                yield line
                last_cap = line

def merge_short_lines(lines):
    buffer = ''
    for line in lines:
        if line == "" or re.match('^\d{2}:\d{2}$', line):
            yield '\n' + line
            continue

        if len(line+buffer) < 80:
            buffer += ' ' + line
        else:
            yield buffer.strip()
            buffer = line
    yield buffer

def convert_vtt_to_text(vtt_content):
    text = remove_tags(vtt_content)
    lines = text.splitlines()
    lines = remove_header(lines)
    lines = merge_duplicates(lines)
    lines = list(lines)
    lines = merge_short_lines(lines)
    return "\n".join(lines)

def sanitize_filename(filename):
    """
    Sanitize the filename by removing special characters and spaces
    """
    # Remove diacritics
    filename = ''.join(c for c in unicodedata.normalize('NFKD', filename) if not unicodedata.combining(c))
    # Replace spaces and special characters with underscores
    filename = re.sub(r'[^\w\-_\. ]', '', filename)
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename.strip('_')

def fetch_transcript(url):
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'vtt',
        'outtmpl': '~/Downloads/%(title)s.%(ext)s',
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        video_title = info['title']
        sanitized_title = sanitize_filename(video_title)

        # Check if transcript already exists
        transcript_path = os.path.expanduser(f"~/Downloads/{sanitized_title}_transcript.txt")
        if os.path.exists(transcript_path):
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = f.read()
            return transcript, sanitized_title

        ydl.download([url])

    # Use glob to find the .vtt file
    vtt_files = glob.glob(os.path.expanduser(f"~/Downloads/{video_title}.en.vtt"))

    if not vtt_files:
        raise FileNotFoundError(f"No .vtt files found for: {video_title}")

    vtt_transcript_path = vtt_files[0]  # Take the first .vtt file found

    with open(vtt_transcript_path, 'r', encoding='utf-8') as f:
        vtt_content = f.read()

    transcript = convert_vtt_to_text(vtt_content)

    os.remove(vtt_transcript_path)
    return transcript, sanitized_title

def generate_notes(transcript, gemini_api_key):
    prompt = f"Please summarize the following transcript and provide key points:\n\n{transcript}"
    system_prompt = f"""You are tasked with creating concise and informative notes from a YouTube video transcript. Your goal is to capture all the main ideas without losing any important information. Follow these instructions carefully:

    1. The transcription of the youtube video will be provided by the user.

    2. Read through the entire transcript carefully to understand the overall structure and main points of the video.

    3. Create notes from the transcript using the following guidelines:
       - Use markdown formatting for your output
       - Utilize bullet points for main ideas
       - Use bold text (**) for key concepts or terms
       - Apply italics (*) for emphasis or definitions when appropriate
       - Employ sub-bullet points (indented) to provide additional information or examples related to a main point

    4. For each main idea or section of the video:
       - Create a top-level bullet point summarizing the main concept
       - Use sub-bullet points to elaborate on details, examples, or supporting information

    5. When a point is particularly important or the speaker uses a memorable phrase:
       - Include an exact quote from the transcript
       - Format the quote using markdown blockquote syntax (>)
       - Place the quote immediately after the relevant bullet point or sub-bullet point

    6. Maintain the overall structure and flow of the video in your notes:
       - Present the information in the same order as it appears in the transcript
       - Use headings (####) h4 to separate major sections if the video has a clear structure

    7. Ensure that no main ideas are lost in the summarization process. Your notes should provide a comprehensive overview of the video's content.

    7.1. If there are any examples mentioned in the video, include all examples with the revelant details. if there are before/after or suggestions mentioned for the examples, include those. don't leave info about the feedbacks said about the examples.

    8. After creating your notes, review them to ensure clarity, coherence, and completeness.

    9. Make sure no point from the video is missing from the notes. Be detailed where needed. I need all the points from the video than making it short.

    10. If possible, create a key points section that summarizes the main ideas in one sentence each for each key point. For example, if the video discusses how the dopamine circuitry in the brain helps us learn behavior, the key point could be: behavior -> reward -> learning. Feel free to create diagrams like this to illustrate the key points.

    11. Enclose your final output within <notes> tags.

    Remember, your goal is to create clear, concise, and well-structured notes that capture the essence of the video without losing any crucial information."""
    os.environ["GEMINI_API_KEY"] = gemini_api_key
    response = completion(model="gemini/gemini-1.5-pro-latest", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], safety_settings=[
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ])
    return response.get('choices', [{}])[0].get('message', {}).get('content', '')

def save_to_file(content, filename):
    filepath = os.path.expanduser(f"~/Downloads/{filename}")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath

def markdown_to_pdf(markdown_content, output_path):
    # Convert both indented and non-indented blockquotes to HTML format
    markdown_content = re.sub(r'^(\s*)>\s*(.+)$', r'\1<blockquote>\2</blockquote>', markdown_content, flags=re.MULTILINE)

    # Use markdown2 for conversion
    html = markdown2.markdown(markdown_content, extras=["fenced-code-blocks"])

    # Define custom CSS
    css = """
    <style>
    @page {
        margin: 1cm;
    }
    body {
        font-family: Arial, Helvetica, sans-serif;
        font-size: 18px;
        line-height: 1.6;
    }
    blockquote {
        border-left: 4px solid #ccc;
        margin: 1em 0;
        padding-left: 1em;
        font-style: italic;
    }
    </style>
    """

    # Combine the CSS with the HTML content
    html_with_css = f"{css}{html}"

    # Use options to specify additional PDF settings
    options = {
        'encoding': 'UTF-8',
        'no-outline': None,
        'quiet': '',
        'enable-local-file-access': None,
        'page-size': 'A4',
    }

    pdfkit.from_string(html_with_css, output_path, options=options)

def main():
    parser = argparse.ArgumentParser(description="Generate notes from YouTube video transcript")
    parser.add_argument("url", help="YouTube video URL", nargs='?')
    parser.add_argument("--gemini-api-key", help="Gemini API key")
    parser.add_argument("--copy-to-clipboard", help="Copy notes to clipboard", action="store_true", default=False)

    args = parser.parse_args()

    if not args.url:
        print("Usage: python script.py <YouTube_URL> --gemini-api-key <API_KEY> [--copy-to-clipboard]")
        print("\nExample:")
        print("python script.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --gemini-api-key YOUR_API_KEY --copy-to-clipboard")
        sys.exit(0)

    gemini_api_key = args.gemini_api_key or os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key:
        print("Error: Gemini API key is required.")
        print("Use --gemini-api-key to provide your API key or set the GEMINI_API_KEY environment variable.")
        sys.exit(1)

    try:
        transcript, sanitized_title = fetch_transcript(args.url)
        transcript_path = os.path.expanduser(f"~/Downloads/{sanitized_title}_transcript.txt")
        if not os.path.exists(transcript_path):
            save_to_file(transcript, f"{sanitized_title}_transcript.txt")

        notes = generate_notes(transcript, gemini_api_key)

        if not notes:
            print("Error: Failed to generate notes. The API response was empty.")
            sys.exit(1)

        # Extract content within <notes> tags
        notes_content = re.search(r'<notes>(.*?)</notes>', notes, re.DOTALL)
        if notes_content:
            notes_to_convert = notes_content.group(1).strip()
        else:
            print("No notes content found")
            sys.exit(1)

        # Save notes content to a text file
        notes_content_path = save_to_file(notes_to_convert, f"{sanitized_title}_notes.txt")
        print(f"Notes content saved to: {notes_content_path}")

        # Generate PDF
        pdf_output_path = os.path.expanduser(f"~/Downloads/{sanitized_title}_notes.pdf")
        markdown_to_pdf(notes_to_convert, pdf_output_path)
        print(f"PDF notes saved to: {pdf_output_path}")

        if args.copy_to_clipboard:
            pyperclip.copy(notes_to_convert)
            print("Notes copied to clipboard.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
