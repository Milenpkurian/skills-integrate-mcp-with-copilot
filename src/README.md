# Mergington High School Activities API

A super simple FastAPI application that allows students to view extracurricular activities and teachers to manage student sign-ups.

## Features

- View all available extracurricular activities
- Teacher sign-in to register and unregister students
- Public activity and participant list

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Configure teacher credentials as environment variables. Do not commit credentials to the repository:

   ```
   export TEACHER_USERNAME=teacher
   export TEACHER_PASSWORD='<choose-a-strong-password>'
   ```

   For local HTTP development only, set `TEACHER_COOKIE_SECURE=false`. The cookie is Secure by default and should remain Secure when the app is served over HTTPS.

3. Run the application from the repository root:

   ```
   uvicorn src.app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                          |
| ------ | ----------------------------------------------------------------- | -------------------------------------------------------------------- |
| POST   | `/auth/login`                                                     | Sign in as a teacher and receive an HttpOnly session cookie          |
| GET    | `/auth/session`                                                   | Check whether the current browser has an active teacher session      |
| POST   | `/auth/logout`                                                    | End the current teacher session                                      |
| GET    | `/activities`                                                     | Get all activities and their current participant lists               |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher-only: register a student for an activity                     |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher-only: unregister a student from an activity               |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Activity and teacher-session data is stored in memory, so it is reset when the server restarts. Configure a unique, strong teacher password outside the repository. Teacher sessions expire after one hour.
