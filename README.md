# UNIGE SmartSync - Syllabus Calendar Generator

UNIGE SmartSync is a small web app built for students at the University of Geneva. It takes a course syllabus (PDF or TXT), finds important dates like exams and deadlines using OpenAI, and turns them into a calendar file you can import into Google Calendar, Apple Calendar, Outlook, etc.

The goal is simple: no more manually copying dates from PDFs into your calendar.

Features

- Upload syllabus files in PDF or TXT format

- Automatic date and deadline extraction using OpenAI

- Export events as a standard .ics calendar file

- Works with Google Calendar, Apple Calendar, Outlook, and more

- Clean and lightweight web interface

Setup
1. Install dependencies
pip install -r requirements.txt

2. Set your OpenAI API key

- Get your API key from OpenAI, then either:

- Create a .env file in the project root:

- OPENAI_API_KEY=your_api_key_here


- Or export it as an environment variable: export OPENAI_API_KEY=your_api_key_here

3. Run the app
python app.py


Then open your browser and go to:

http://localhost:5001


How to use

- Click “Choose Syllabus File” (or drag and drop a file)

- Select a PDF or TXT syllabus

- Click “Generate Calendar (.ics)”

- Wait a few seconds while the dates are extracted

- The calendar file will download automatically

- Import it into your favorite calendar app


How it works (behind the scenes)

- File upload – accepts PDF or TXT files up to 16 MB

- Text extraction

- PDFs are processed with PyPDF2

- TXT files are read directly

- AI processing – the extracted text is sent to OpenAI (GPT-4o-mini) with a prompt that looks for exams, deadlines, assignments, etc.

- Calendar generation – detected events are converted into a valid .ics file

- Download – the file is returned to the user

Requirements

- Python 3.7 or newer

- OpenAI API key

- Flask and other dependencies (see requirements.txt)

```
SmartSync/
├── app.py              # Flask backend application
├── templates/
│   └── index.html      # Frontend HTML/CSS/JS
├── requirements.txt    # Python dependencies
├── .env.example       # Example environment file
└── README.md          # This file
```

Notes

- The app uses OpenAI's `gpt-4o-mini` model for cost efficiency
- Large syllabus files (>50,000 characters) are truncated to stay within API limits
- All-day events are used when no specific time is found in the syllabus
- Events with invalid dates are automatically skipped

