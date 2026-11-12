"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hmac
import os
from pathlib import Path
import secrets
import time

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

SESSION_COOKIE_NAME = "teacher_session"
SESSION_MAX_AGE_SECONDS = 60 * 60
SESSION_COOKIE_SECURE = os.getenv("TEACHER_COOKIE_SECURE", "true").lower() == "true"
teacher_sessions: dict[str, float] = {}


class TeacherCredentials(BaseModel):
    username: str
    password: str


def has_teacher_session(request: Request) -> bool:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        return False

    expires_at = teacher_sessions.get(token)
    if expires_at is None:
        return False
    if expires_at <= time.time():
        teacher_sessions.pop(token, None)
        return False

    return True


def require_teacher(request: Request) -> None:
    if not has_teacher_session(request):
        raise HTTPException(status_code=401, detail="Teacher login required")


# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/auth/login")
def teacher_login(credentials: TeacherCredentials, response: Response):
    expected_username = os.getenv("TEACHER_USERNAME")
    expected_password = os.getenv("TEACHER_PASSWORD")
    if not expected_username or not expected_password:
        raise HTTPException(
            status_code=503,
            detail="Teacher login is not configured on the server"
        )

    username_matches = hmac.compare_digest(
        credentials.username, expected_username
    )
    password_matches = hmac.compare_digest(
        credentials.password, expected_password
    )
    if not (username_matches and password_matches):
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    now = time.time()
    for token, expires_at in list(teacher_sessions.items()):
        if expires_at <= now:
            del teacher_sessions[token]

    token = secrets.token_urlsafe(32)
    teacher_sessions[token] = now + SESSION_MAX_AGE_SECONDS
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="strict",
    )
    return {"message": "Teacher login successful"}


@app.get("/auth/session")
def get_teacher_session(request: Request):
    return {"authenticated": has_teacher_session(request)}


@app.post("/auth/logout")
def teacher_logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is not None:
        teacher_sessions.pop(token, None)
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="strict",
    )
    return {"message": "Teacher logged out"}


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup",
          dependencies=[Depends(require_teacher)])
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister",
            dependencies=[Depends(require_teacher)])
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
