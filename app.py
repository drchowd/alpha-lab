import os
import json
import re
from datetime import datetime, timedelta
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
import PyPDF2
import io
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'txt'}

# Initialize OpenAI client
# Add your OpenAI API key here:
# Option 1: Set it as an environment variable: export OPENAI_API_KEY="your_api_key_here"
# Option 2: Create a .env file in the project root with: OPENAI_API_KEY=your_api_key_here
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in a .env file or as an environment variable.")
client = OpenAI(api_key=api_key)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_text_from_pdf(file_path):
    """Extract text from PDF file."""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def extract_text_from_txt(file_path):
    """Extract text from TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        raise Exception(f"Error reading text file: {str(e)}")

def extract_events_with_ai(text):
    """Call OpenAI API to extract events from syllabus text."""
    system_prompt = """You are parsing an academic course syllabus. Extract all important dates and deadlines (exams, quizzes, assignments, projects, due dates, presentations, classes, etc.) and return them as strict JSON array.

CRITICAL INSTRUCTIONS:
1. COURSE NAME: FIRST, identify the course name, course code, or subject from the syllabus (e.g., "Introduction to Computer Science", "CS 101", "Physics 201", "Calculus I"). ALWAYS include this course identifier in event titles. For class sessions, use format like "CS 101 - Class Session" or "Introduction to Computer Science - Lecture", NOT just "Class Session".

2. RECURRING EVENTS: If the syllabus mentions recurring events (e.g., "Classes every Friday from September 1 to December 15", "Weekly lab sessions on Mondays until November 30"), you MUST expand these into individual events for EACH occurrence. Do NOT create a single event - create separate events for each date in the recurring series. Each recurring event should include the course name in its title.

3. Each event should have:
- title (string, MUST include the course name/code when available. Examples: "CS 101 - Midterm Exam", "Physics 201 - Assignment 1 Due", "Introduction to Biology - Lab Session", "Calculus I - Class Session". For non-class events, still include course name if it makes sense: "CS 101 - Final Project Due")
- date (string, ISO format YYYY-MM-DD) - REQUIRED
- time (string, HH:MM format in 24-hour time, or null if no time specified)
- location (string, room number, building name, or location if mentioned in syllabus, or null if not specified)
- description (string, any additional details from the syllabus such as topics covered, requirements, submission instructions, etc., or null if none)

4. Extract ALL information available: If the syllabus mentions a location (room, building, online platform), include it. If there are details about what will be covered, submission methods, or other relevant information, include it in the description.

Return ONLY valid JSON array, no markdown, no code blocks, just the JSON array. Example format:
[
  {"title": "CS 101 - Midterm Exam", "date": "2024-10-15", "time": "14:00", "location": "Room 101", "description": "Covers chapters 1-5. Bring calculator."},
  {"title": "Physics 201 - Assignment 1 Due", "date": "2024-09-20", "time": null, "location": null, "description": "Submit via Canvas"},
  {"title": "Introduction to Biology - Class Session", "date": "2024-09-06", "time": "10:00", "location": "Building A, Room 205", "description": "Introduction to course topics"},
  {"title": "Introduction to Biology - Class Session", "date": "2024-09-13", "time": "10:00", "location": "Building A, Room 205", "description": null}
]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract all important dates and deadlines from this syllabus:\n\n{text}"}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'```\s*$', '', content, flags=re.MULTILINE)
        
        # Parse JSON
        events = json.loads(content)
        return events
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response from OpenAI: {str(e)}")
    except Exception as e:
        raise Exception(f"Error calling OpenAI API: {str(e)}")

def generate_ics_file(events, filename="syllabus_deadlines.ics"):
    """Generate .ics calendar file from events list."""
    ics_content = ["BEGIN:VCALENDAR",
                   "VERSION:2.0",
                   "PRODID:-//SmartSync//Syllabus Calendar//EN",
                   "CALSCALE:GREGORIAN",
                   "METHOD:PUBLISH"]
    
    dtstamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    
    for idx, event in enumerate(events):
        title = event.get('title', 'Untitled Event')
        date_str = event.get('date', '')
        time_str = event.get('time')
        location = event.get('location')
        description = event.get('description', '')
        
        # Validate date format
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue  # Skip invalid dates
        
        # Generate unique ID
        uid = f"syllabus-{idx}-{date_str.replace('-', '')}@smartsync"
        
        # Format date/time
        if time_str:
            # Has time - use DTSTART and DTEND with time
            try:
                time_obj = datetime.strptime(time_str, "%H:%M")
                dtstart = date_obj.replace(hour=time_obj.hour, minute=time_obj.minute).strftime("%Y%m%dT%H%M%S")
                # Default to 1 hour duration
                dtend_obj = date_obj.replace(hour=time_obj.hour, minute=time_obj.minute)
                dtend_obj = dtend_obj.replace(hour=(dtend_obj.hour + 1) % 24) if dtend_obj.hour < 23 else dtend_obj.replace(hour=23, minute=59)
                dtend = dtend_obj.strftime("%Y%m%dT%H%M%S")
            except ValueError:
                # Invalid time format, treat as all-day
                dtstart = date_obj.strftime("%Y%m%d")
                # All-day events: DTEND is exclusive (next day)
                dtend = (date_obj + timedelta(days=1)).strftime("%Y%m%d")
        else:
            # All-day event
            dtstart = date_obj.strftime("%Y%m%d")
            # All-day events: DTEND is exclusive (next day)
            dtend = (date_obj + timedelta(days=1)).strftime("%Y%m%d")
        
        # Escape special characters in text fields
        def escape_ics_text(text):
            text = str(text).replace('\\', '\\\\')
            text = text.replace(',', '\\,')
            text = text.replace(';', '\\;')
            text = text.replace('\n', '\\n')
            return text
        
        ics_content.append("BEGIN:VEVENT")
        ics_content.append(f"UID:{uid}")
        ics_content.append(f"DTSTAMP:{dtstamp}")
        
        if time_str:
            ics_content.append(f"DTSTART:{dtstart}")
            ics_content.append(f"DTEND:{dtend}")
        else:
            ics_content.append(f"DTSTART;VALUE=DATE:{dtstart}")
            ics_content.append(f"DTEND;VALUE=DATE:{dtend}")
        
        ics_content.append(f"SUMMARY:{escape_ics_text(title)}")
        if location:
            ics_content.append(f"LOCATION:{escape_ics_text(location)}")
        if description:
            ics_content.append(f"DESCRIPTION:{escape_ics_text(description)}")
        ics_content.append("END:VEVENT")
    
    ics_content.append("END:VCALENDAR")
    
    return "\r\n".join(ics_content)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload PDF or TXT files only.'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Extract text based on file type
        if filename.rsplit('.', 1)[1].lower() == 'pdf':
            text = extract_text_from_pdf(file_path)
        else:
            text = extract_text_from_txt(file_path)
        
        if not text or len(text.strip()) == 0:
            return jsonify({'error': 'Could not extract text from file. File may be empty or corrupted.'}), 400
        
        # Truncate text if too long (OpenAI has token limits)
        max_chars = 50000  # Reasonable limit
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Text truncated due to length...]"
        
        # Extract events using OpenAI
        events = extract_events_with_ai(text)
        
        if not events or len(events) == 0:
            return jsonify({'error': 'No events found in the syllabus. Please check if the file contains date information.'}), 400
        
        # Generate ICS file
        ics_content = generate_ics_file(events)
        
        # Clean up uploaded file
        os.remove(file_path)
        
        # Create in-memory file for download
        ics_file = io.BytesIO(ics_content.encode('utf-8'))
        ics_file.seek(0)
        
        return send_file(
            ics_file,
            mimetype='text/calendar',
            as_attachment=True,
            download_name='syllabus_deadlines.ics'
        )
    
    except Exception as e:
        # Clean up file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)

