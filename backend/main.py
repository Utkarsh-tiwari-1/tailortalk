from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from pydantic import BaseModel
from datetime import datetime, timedelta, time
from typing import List, Optional
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
import re

service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
if service_account_json:
    os.makedirs("backend", exist_ok=True)
    with open("backend/service_account.json", "w") as f:
        f.write(service_account_json)
load_dotenv()

app = FastAPI()

# Allow CORS for local development and Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to your service account key
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'service_account.json')
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Set your calendar ID here (can be primary or a specific calendar)
CALENDAR_ID = 'primary'  # You can replace with your test calendar ID

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_calendar_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    return service

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/events")
def list_events():
    service = get_calendar_service()
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    return {"events": events}

@app.get("/upcoming")
def get_upcoming_events():
    service = get_calendar_service()
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        maxResults=5,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    return {"events": events}

class AvailabilityRequest(BaseModel):
    date: str  # 'YYYY-MM-DD'
    duration_minutes: Optional[int] = 60

class BookRequest(BaseModel):
    start: str  # ISO format
    end: str    # ISO format
    summary: str
    description: Optional[str] = None
    attendees: Optional[List[str]] = []

class ChatRequest(BaseModel):
    message: str

@app.post("/availability")
def get_availability(req: AvailabilityRequest):
    service = get_calendar_service()
    date = datetime.strptime(req.date, "%Y-%m-%d")
    start_of_day = datetime.combine(date, time(9, 0))
    end_of_day = datetime.combine(date, time(17, 0))
    duration = timedelta(minutes=int(req.duration_minutes or 60))

    # Get all events for the day
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_of_day.isoformat() + 'Z',
        timeMax=end_of_day.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    # Build list of busy slots
    busy = []
    for event in events:
        start = event['start'].get('dateTime')
        end = event['end'].get('dateTime')
        if start and end:
            busy.append((datetime.fromisoformat(start.replace('Z', '')), datetime.fromisoformat(end.replace('Z', ''))))

    # Find available slots
    slots = []
    current = start_of_day
    while current + duration <= end_of_day:
        slot_start = current
        slot_end = current + duration
        overlap = any(
            (slot_start < b_end and slot_end > b_start)
            for b_start, b_end in busy
        )
        if not overlap:
            slots.append({
                "start": slot_start.isoformat(),
                "end": slot_end.isoformat()
            })
        current += duration
    return {"available_slots": slots}

@app.post("/book")
def book_event(req: BookRequest):
    service = get_calendar_service()
    event = {
        'summary': req.summary,
        'description': req.description or '',
        'start': {'dateTime': req.start, 'timeZone': 'UTC'},
        'end': {'dateTime': req.end, 'timeZone': 'UTC'},
        'attendees': [],
    }
    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return {"event": created_event}

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    user_message = req.message
    print(f"Received message: {user_message}")
    if not user_message:
        return {"response": "Please enter a message."}
    try:
        msg_lower = user_message.lower()
        if any(word in msg_lower for word in ["available", "free slot", "free time", "availability", "when can i book", "open slot"]):
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", user_message)
            if date_match:
                date_str = date_match.group(1)
            elif "tomorrow" in msg_lower:
                date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
            avail_req = AvailabilityRequest(date=date_str)
            result = get_availability(avail_req)
            slots = result["available_slots"]
            if slots:
                slot_str = "\n".join([f"{s['start']} to {s['end']}" for s in slots])
                reply = f"Here are the available slots for {date_str}:\n{slot_str}"
            else:
                reply = f"Sorry, there are no available slots for {date_str}."
            return {"response": reply}
        elif any(word in msg_lower for word in ["book", "schedule", "reserve", "set up meeting"]):
            # Remove dateparser, use only regex/defaults
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", user_message)
            time_match = re.search(r"(\d{1,2}(:\d{2})? ?(am|pm)?)", user_message, re.IGNORECASE)
            duration_match = re.search(r"(\d+) ?(hour|hr|minute|min)", user_message)
            emails = re.findall(r"[\w\.-]+@[\w\.-]+", user_message)
            title_match = re.search(r'"([^"]+)"|\'([^\']+)\'', user_message)
            summary_match = re.search(r"with ([\w ]+)", user_message)
            date_str = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
            hour = 9
            minute = 0
            if time_match:
                t = time_match.group(1).replace(" ","").lower()
                hour_search = re.search(r"\d{1,2}", t)
                if hour_search:
                    hour = int(hour_search.group(0))
                if "am" in t or "pm" in t:
                    if "pm" in t and hour != 12:
                        hour += 12
                    if "am" in t and hour == 12:
                        hour = 0
                if ":" in t:
                    minute_part = t.split(":")[1] if len(t.split(":")) > 1 else "0"
                    if minute_part.isdigit():
                        minute = int(minute_part)
            start_dt = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
            duration = 60
            if duration_match:
                val = int(duration_match.group(1))
                if "min" in duration_match.group(2):
                    duration = val
                else:
                    duration = val * 60
            end_dt = start_dt + timedelta(minutes=duration)
            if title_match:
                summary = title_match.group(1) or title_match.group(2)
            elif summary_match:
                summary = summary_match.group(1).strip().title()
            else:
                summary = "Meeting"
            attendee_note = f" Attendees: {', '.join(emails)}." if emails else ""
            book_req = BookRequest(
                start=start_dt.isoformat(),
                end=end_dt.isoformat(),
                summary=summary,
                description=f"Booked via TailorTalk bot.{attendee_note}",
                attendees=[]
            )
            result = book_event(book_req)
            reply = f"Your meeting '{summary}' is booked for {start_dt.strftime('%Y-%m-%d %I:%M %p')} to {end_dt.strftime('%I:%M %p')}!"
            if emails:
                reply += f" (Attendees: {', '.join(emails)})"
            return {"response": reply}
        elif any(word in msg_lower for word in [
            "upcoming", "upcomming", "show my bookings", "my meetings", "next events", "upcoming meetings", "upcomming meetings"
        ]):
            result = get_upcoming_events()
            events = result["events"]
            if events:
                event_lines = []
                for e in events:
                    start = e['start'].get('dateTime', e['start'].get('date', ''))
                    summary = e.get('summary', 'No Title')
                    event_lines.append(f"{summary} at {start}")
                reply = "Here are your next bookings:\n" + "\n".join(event_lines)
            else:
                reply = "You have no upcoming bookings."
            return {"response": reply}
        else:
            openrouter_key = os.getenv("OPENROUTER_API_KEY")
            try:
                llm = ChatOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=openrouter_key,
                    model="openai/gpt-4o"
                )
                system_prompt = """
                You are a helpful assistant for booking appointments on Google Calendar. 
                You can check availability and book meetings. 
                If the user asks to book, extract the date, time, and details. 
                If the user asks for available slots, extract the date.
                """
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message)
                ]
                response = llm(messages)
            except Exception as e1:
                try:
                    llm = ChatOpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=openrouter_key,
                        model="google/gemini-pro"
                    )
                    response = llm(messages)
                except Exception as e2:
                    llm = ChatOpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=openrouter_key,
                        model="openai/gpt-4o-mini"
                    )
                    response = llm(messages)
            reply = response.content
            print(f"LLM reply: {reply}")
            return {"response": reply}
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        return {"error": str(e)}
