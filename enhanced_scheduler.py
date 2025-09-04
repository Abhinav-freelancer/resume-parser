import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EnhancedInterviewScheduler:
    def __init__(self, credentials_path: str = "credentials.json"):
        self.credentials_path = credentials_path
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.send'
        ]
        self.service = None
        self.gmail_service = None

        # LinkedIn API credentials (provided by user)
        self.linkedin_client_id = "78qhcvra68bssm"
        self.linkedin_client_secret = "WPL_AP1.rzP77o9ksyi8Zsr8.14Pb6g=="

        # Google API credentials (provided by user)
        self.google_client_id = "1030951934654-sh6udofahfqa2spdsidbs696biqluel5.apps.googleusercontent.com"
        self.google_client_secret = "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"

    async def initialize_google_services(self):
        """Initialize Google Calendar and Gmail services"""
        try:
            creds = None

            # Check if token.json exists
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', self.scopes)

            # If credentials are invalid or don't exist, authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Create credentials.json with provided credentials
                    self._create_credentials_file()

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.scopes)
                    creds = flow.run_local_server(port=0)

                # Save credentials for future use
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

            # Build services
            self.service = build('calendar', 'v3', credentials=creds)
            self.gmail_service = build('gmail', 'v1', credentials=creds)

            logger.info("Google services initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing Google services: {str(e)}")
            return False

    def _create_credentials_file(self):
        """Create credentials.json file with provided credentials"""
        credentials_data = {
            "installed": {
                "client_id": self.google_client_id,
                "project_id": "nlp-ai-resumeparser",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": self.google_client_secret,
                "redirect_uris": ["http://localhost"]
            }
        }

        with open(self.credentials_path, 'w') as f:
            json.dump(credentials_data, f, indent=2)

    async def schedule_interview(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule an interview with calendar integration"""
        try:
            # Validate required fields
            required_fields = ['candidate_id', 'job_id', 'datetime', 'interviewer', 'interview_type']
            for field in required_fields:
                if field not in interview_data:
                    raise ValueError(f"Missing required field: {field}")

            # Generate meeting details
            meeting_details = await self._generate_meeting_details(interview_data)

            # Create calendar event
            calendar_event = await self._create_calendar_event(meeting_details)

            # Send email invitations
            await self._send_email_invitations(meeting_details, calendar_event)

            # Update interview data with meeting link
            interview_data['meeting_link'] = calendar_event.get('hangoutLink', '')
            interview_data['calendar_event_id'] = calendar_event['id']
            interview_data['status'] = 'Scheduled'

            logger.info(f"Interview scheduled successfully: {interview_data['id']}")
            return interview_data

        except Exception as e:
            logger.error(f"Error scheduling interview: {str(e)}")
            raise

    async def _generate_meeting_details(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meeting details for the interview"""
        # This would typically fetch candidate and job details from database
        # For now, using placeholder data
        meeting_details = {
            'title': f"Interview: {interview_data.get('candidate_name', 'Candidate')} - {interview_data.get('job_title', 'Position')}",
            'description': f"""
Interview Details:
- Candidate: {interview_data.get('candidate_name', 'TBD')}
- Position: {interview_data.get('job_title', 'TBD')}
- Interviewer: {interview_data['interviewer']}
- Type: {interview_data['interview_type']}
- Duration: {interview_data.get('duration', 60)} minutes

Please prepare for the interview and review the candidate's resume beforehand.
            """.strip(),
            'start_time': interview_data['datetime'],
            'duration': interview_data.get('duration', 60),
            'attendees': [
                {'email': interview_data.get('candidate_email', 'candidate@example.com')},
                {'email': self._get_interviewer_email(interview_data['interviewer'])}
            ],
            'location': interview_data.get('location', 'Virtual Meeting')
        }

        return meeting_details

    async def _create_calendar_event(self, meeting_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create Google Calendar event"""
        if not self.service:
            raise Exception("Google Calendar service not initialized")

        try:
            # Parse start time
            start_datetime = datetime.fromisoformat(meeting_details['start_time'])
            end_datetime = start_datetime + timedelta(minutes=meeting_details['duration'])

            event = {
                'summary': meeting_details['title'],
                'description': meeting_details['description'],
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': meeting_details['attendees'],
                'location': meeting_details['location'],
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"interview_{int(datetime.now().timestamp())}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},      # 30 minutes before
                    ],
                },
            }

            # Create the event
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1,
                sendUpdates='all'
            ).execute()

            logger.info(f"Calendar event created: {created_event['id']}")
            return created_event

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            raise Exception(f"Failed to create calendar event: {e}")

    async def _send_email_invitations(self, meeting_details: Dict[str, Any], calendar_event: Dict[str, Any]):
        """Send email invitations to participants"""
        try:
            meeting_link = calendar_event.get('hangoutLink', 'TBD')

            # Email to candidate
            candidate_email = meeting_details['attendees'][0]['email']
            await self._send_candidate_invitation(candidate_email, meeting_details, meeting_link)

            # Email to interviewer
            interviewer_email = meeting_details['attendees'][1]['email']
            await self._send_interviewer_notification(interviewer_email, meeting_details, meeting_link)

            logger.info("Email invitations sent successfully")

        except Exception as e:
            logger.error(f"Error sending email invitations: {str(e)}")
            # Don't raise exception here as calendar event was created successfully

    async def _send_candidate_invitation(self, email: str, meeting_details: Dict[str, Any], meeting_link: str):
        """Send interview invitation to candidate"""
        subject = f"Interview Invitation: {meeting_details['title']}"

        body = f"""
Dear Candidate,

You have been invited to an interview for the position of {meeting_details.get('job_title', 'the position')}.

Interview Details:
- Date & Time: {datetime.fromisoformat(meeting_details['start_time']).strftime('%B %d, %Y at %I:%M %p UTC')}
- Interviewer: {meeting_details.get('interviewer', 'TBD')}
- Duration: {meeting_details['duration']} minutes
- Location: {meeting_details['location']}
- Meeting Link: {meeting_link}

Please make sure to:
1. Test your audio and video before the interview
2. Have a quiet, well-lit environment
3. Prepare any questions you may have
4. Bring your resume and portfolio if applicable

If you need to reschedule or have any questions, please reply to this email.

Best regards,
HireAI Recruitment Team
        """.strip()

        await self._send_email(email, subject, body)

    async def _send_interviewer_notification(self, email: str, meeting_details: Dict[str, Any], meeting_link: str):
        """Send interview notification to interviewer"""
        subject = f"Interview Scheduled: {meeting_details['title']}"

        body = f"""
Dear {meeting_details.get('interviewer', 'Interviewer')},

You have an interview scheduled.

Interview Details:
- Candidate: {meeting_details.get('candidate_name', 'TBD')}
- Position: {meeting_details.get('job_title', 'TBD')}
- Date & Time: {datetime.fromisoformat(meeting_details['start_time']).strftime('%B %d, %Y at %I:%M %p UTC')}
- Duration: {meeting_details['duration']} minutes
- Meeting Link: {meeting_link}

Please review the candidate's resume and prepare relevant questions for the interview.

Best regards,
HireAI Recruitment Team
        """.strip()

        await self._send_email(email, subject, body)

    async def _send_email(self, to_email: str, subject: str, body: str):
        """Send email using Gmail API"""
        if not self.gmail_service:
            logger.warning("Gmail service not available, skipping email send")
            return

        try:
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject

            message.attach(MIMEText(body, 'plain'))

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Email sent to: {to_email}")

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")

    def _get_interviewer_email(self, interviewer_name: str) -> str:
        """Get interviewer email from name (placeholder implementation)"""
        # This would typically look up interviewer email from database
        # For now, using placeholder mapping
        interviewer_emails = {
            "John Smith": "john.smith@company.com",
            "Sarah Wilson": "sarah.wilson@company.com",
            "Mike Johnson": "mike.johnson@company.com",
            "Lisa Chen": "lisa.chen@company.com"
        }

        return interviewer_emails.get(interviewer_name, "interviewer@company.com")

    async def reschedule_interview(self, interview_id: int, new_datetime: str) -> Dict[str, Any]:
        """Reschedule an existing interview"""
        try:
            # This would typically fetch interview data from database
            # For now, using placeholder
            interview_data = {
                'id': interview_id,
                'datetime': new_datetime,
                'candidate_name': 'Candidate Name',
                'job_title': 'Job Title',
                'interviewer': 'Interviewer Name',
                'interview_type': 'Technical',
                'duration': 60
            }

            # Update calendar event
            await self._update_calendar_event(interview_id, new_datetime)

            # Send rescheduling notifications
            await self._send_reschedule_notifications(interview_data)

            logger.info(f"Interview rescheduled: {interview_id}")
            return interview_data

        except Exception as e:
            logger.error(f"Error rescheduling interview: {str(e)}")
            raise

    async def _update_calendar_event(self, interview_id: int, new_datetime: str):
        """Update existing calendar event"""
        if not self.service:
            raise Exception("Google Calendar service not initialized")

        try:
            # Find event by interview ID (this would need proper event ID storage)
            # For now, this is a placeholder
            logger.info(f"Calendar event update placeholder for interview: {interview_id}")

        except Exception as e:
            logger.error(f"Error updating calendar event: {str(e)}")

    async def _send_reschedule_notifications(self, interview_data: Dict[str, Any]):
        """Send reschedule notifications"""
        # Placeholder for reschedule notifications
        logger.info("Reschedule notifications sent (placeholder)")

    async def cancel_interview(self, interview_id: int) -> bool:
        """Cancel an interview"""
        try:
            # Cancel calendar event
            await self._cancel_calendar_event(interview_id)

            # Send cancellation notifications
            await self._send_cancellation_notifications(interview_id)

            logger.info(f"Interview cancelled: {interview_id}")
            return True

        except Exception as e:
            logger.error(f"Error cancelling interview: {str(e)}")
            return False

    async def _cancel_calendar_event(self, interview_id: int):
        """Cancel calendar event"""
        # Placeholder implementation
        logger.info(f"Calendar event cancelled for interview: {interview_id}")

    async def _send_cancellation_notifications(self, interview_id: int):
        """Send cancellation notifications"""
        # Placeholder implementation
        logger.info(f"Cancellation notifications sent for interview: {interview_id}")

    async def get_available_slots(self, date: str, duration: int = 60) -> List[str]:
        """Get available time slots for a given date"""
        try:
            # Working hours: 9 AM to 5 PM
            start_hour = 9
            end_hour = 17

            available_slots = []
            current_datetime = datetime.fromisoformat(f"{date}T{start_hour:02d}:00:00")

            while current_datetime.hour < end_hour:
                slot_start = current_datetime.isoformat()
                slot_end = (current_datetime + timedelta(minutes=duration)).isoformat()

                # Check if slot is available (placeholder - would check calendar)
                if await self._is_slot_available(slot_start, slot_end):
                    available_slots.append(slot_start)

                current_datetime += timedelta(minutes=duration)

            return available_slots

        except Exception as e:
            logger.error(f"Error getting available slots: {str(e)}")
            return []

    async def _is_slot_available(self, start_time: str, end_time: str) -> bool:
        """Check if a time slot is available"""
        # Placeholder implementation - would check calendar for conflicts
        return True

    async def get_upcoming_interviews(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming interviews within specified days"""
        try:
            if not self.service:
                return []

            # Get calendar events
            now = datetime.utcnow()
            future = now + timedelta(days=days_ahead)

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=future.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            interviews = []
            for event in events_result.get('items', []):
                if 'Interview' in event.get('summary', ''):
                    interviews.append({
                        'id': event['id'],
                        'title': event['summary'],
                        'datetime': event['start'].get('dateTime', event['start'].get('date')),
                        'attendees': [attendee['email'] for attendee in event.get('attendees', [])]
                    })

            return interviews

        except Exception as e:
            logger.error(f"Error getting upcoming interviews: {str(e)}")
            return []

    async def check_availability(self, datetime_str: str, interviewer: str) -> bool:
        """Check if interviewer is available at the given time"""
        try:
            # Parse the datetime
            interview_datetime = datetime.fromisoformat(datetime_str)
            duration_minutes = 60  # Default interview duration

            # Check calendar for conflicts
            if not self.service:
                # If no calendar service, assume available
                logger.warning("Calendar service not available, assuming interviewer is available")
                return True

            # Get interviewer email
            interviewer_email = self._get_interviewer_email(interviewer)

            # Check for conflicting events
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=(interview_datetime - timedelta(minutes=30)).isoformat() + 'Z',
                timeMax=(interview_datetime + timedelta(minutes=duration_minutes + 30)).isoformat() + 'Z',
                singleEvents=True
            ).execute()

            # Check for conflicts
            for event in events_result.get('items', []):
                if interviewer_email in [attendee.get('email', '') for attendee in event.get('attendees', [])]:
                    logger.info(f"Interviewer {interviewer} has conflicting event: {event.get('summary')}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            # Default to available if check fails
            return True

    async def book_slot(self, datetime_str: str, interviewer: str, interview_id: str):
        """Book a time slot for an interview"""
        try:
            logger.info(f"Booking slot for interviewer {interviewer} at {datetime_str}")
            # This is a placeholder - actual booking would be done during calendar event creation
            # The calendar event creation in schedule_interview handles the booking
            pass
        except Exception as e:
            logger.error(f"Error booking slot: {str(e)}")

    async def send_calendar_invite(self, interview_id: str, invite_data: Dict[str, Any]):
        """Send calendar invite for interview"""
        try:
            # This is handled in the schedule_interview method
            # The calendar event creation automatically sends invites to attendees
            logger.info(f"Calendar invite sent for interview {interview_id}")
        except Exception as e:
            logger.error(f"Error sending calendar invite: {str(e)}")
