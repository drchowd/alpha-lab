# UNIGE SmartSync - Syllabus Calendar Generator

A web application for the University of Geneva (UNIGE) that extracts important dates and deadlines from course syllabi (PDF or TXT) using OpenAI's ChatGPT API and generates downloadable .ics calendar files.

## Features

- 📄 Upload PDF or TXT syllabus files
- 🤖 AI-powered date extraction using OpenAI GPT
- 📅 Generate .ics calendar files compatible with Google Calendar, Apple Calendar, and Outlook
- 🎨 Clean, modern web interface

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up OpenAI API key:**
   - Get your API key from [OpenAI](https://platform.openai.com/api-keys)
   - Create a `.env` file in the project root:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```
   - Or export it as an environment variable:
     ```bash
     export OPENAI_API_KEY=your_api_key_here
     ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open your browser:**
   Navigate to `http://localhost:5001`

## Usage

1. Click "Choose Syllabus File" or drag and drop a PDF or TXT file
2. Click "Generate Calendar (.ics)"
3. Wait for processing (the AI will extract dates from your syllabus)
4. The .ics file will automatically download
5. Import the file into your preferred calendar application

## How It Works

1. **File Upload**: Accepts PDF or TXT files up to 16MB
2. **Text Extraction**: 
   - PDFs: Uses PyPDF2 to extract text
   - TXT: Reads file directly
3. **AI Processing**: Sends extracted text to OpenAI GPT-4o-mini with a specialized prompt to identify dates, deadlines, exams, assignments, etc.
4. **Calendar Generation**: Converts the extracted events into a valid .ics (iCalendar) format
5. **Download**: Returns the .ics file for the user to download

## Requirements

- Python 3.7+
- OpenAI API key
- Flask and dependencies (see `requirements.txt`)

## File Structure

```
SmartSync/
├── app.py              # Flask backend application
├── templates/
│   └── index.html      # Frontend HTML/CSS/JS
├── requirements.txt    # Python dependencies
├── .env.example       # Example environment file
└── README.md          # This file
```

## Notes

- The app uses OpenAI's `gpt-4o-mini` model for cost efficiency
- Large syllabus files (>50,000 characters) are truncated to stay within API limits
- All-day events are used when no specific time is found in the syllabus
- Events with invalid dates are automatically skipped

