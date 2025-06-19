import os
import sys

# Ensure Google can see the credentials in the frozen bundle
if getattr(sys, 'frozen', False):
    # When bundled, files live in _MEIPASS
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

keyfile = os.path.join(base_path, 'driveuploader-456317-fdcff069c6d3.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = keyfile

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Path to your downloaded JSON key file (relative path)
SERVICE_ACCOUNT_FILE = keyfile

# Google Drive folder ID
FOLDER_ID = '1bokrCeqwgYY7qhiMFcNV4jiwdUSp_Foi'

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate using the service account
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

drive_service = build('drive', 'v3', credentials=credentials)

def upload_file_to_drive(file_path):
    """Uploads a file to Google Drive and returns the public link."""
    file_name = os.path.basename(file_path)

    file_metadata = {
        'name': file_name,
        'parents': [FOLDER_ID]
    }

    media = MediaFileUpload(file_path, resumable=True)

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = file.get('id')

    # Make the file public
    drive_service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    # Return the direct access link
    return f"https://drive.google.com/uc?id={file_id}"
