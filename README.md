# YouTube Notes Generator

This Python script generates notes from YouTube video transcripts using AI. It fetches the transcript, generates summarized notes, and saves them in both text and PDF formats.

## Features

- Fetch transcripts from YouTube videos
- Generate summarized notes using AI (Gemini)
- Save notes in text and PDF formats
- Copy notes to clipboard (optional)

## Prerequisites

- Python 3.11+
- ffmpeg (required for yt-dlp)
- wkhtmltopdf (required for pdfkit)

## Required Packages

- yt-dlp
- litellm
- python-dotenv
- markdown2
- pdfkit
- pyperclip

## Installation

You can install this project using either pip or Poetry.

### Installing ffmpeg and wkhtmltopdf

1. Install ffmpeg:
   - On macOS (using Homebrew): `brew install ffmpeg`
   - On Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - On Windows: Download from https://ffmpeg.org/download.html and add to PATH

2. Install wkhtmltopdf:
   - On macOS (using Homebrew): `brew install wkhtmltopdf`
   - On Ubuntu/Debian: `sudo apt-get install wkhtmltopdf`
   - On Windows: Download from https://wkhtmltopdf.org/downloads.html and add to PATH

### Using pip

1. Clone the repository:
   ```
   git clone https://github.com/risonsimon/youtube-notes.git
   cd youtube-notes
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install yt-dlp litellm python-dotenv markdown2 pdfkit pyperclip
   ```

### Using Poetry

Poetry is a modern dependency management and packaging tool for Python projects.

1. Clone the repository:
   ```
   git clone https://github.com/risonsimon/youtube-notes.git
   cd youtube-notes
   ```

2. Install Poetry if you haven't already:
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Initialize a new Poetry project:
   ```
   poetry init
   ```

4. Add the required dependencies:
   ```
   poetry add yt-dlp litellm python-dotenv markdown2 pdfkit pyperclip
   ```

5. Install the dependencies:
   ```
   poetry install
   ```

## Usage

1. Activate your virtual environment (if using pip) or run `poetry shell` (if using Poetry).

2. Run the script with the following command:
   ```
   python youtube-notes/index.py <YouTube_URL> --gemini-api-key <YOUR_GEMINI_API_KEY> [--copy-to-clipboard]
   ```

   Replace `<YouTube_URL>` with the URL of the video you want to generate notes for, and `<YOUR_GEMINI_API_KEY>` with your actual Gemini API key.

   Use the `--copy-to-clipboard` flag if you want to copy the generated notes to your clipboard.

3. The script will generate a transcript file, a text file with the notes, and a PDF file with the formatted notes in your Downloads folder.

## Environment Variables

You can set the `GEMINI_API_KEY` environment variable instead of passing it as a command-line argument. Create a `.env` file in the project root directory with the following content:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
