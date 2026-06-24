import os
import sys
import json
import zipfile
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import webbrowser

from src.db.supabase_client import get_db

# Google API Scopes: Metadata read and full upload access to Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.metadata.readonly']

# Determine credential storage paths in AppData (frozen vs development)
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TOKEN_FILE = os.path.join(APP_DIR, "google_token.json")
CLIENT_SECRETS_FILE = os.path.join(APP_DIR, "client_secrets.json")

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'code' in params:
            # Successfully captured the authorization code
            self.server.auth_code = params['code'][0]
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        background-color: #F8FAFC;
                        color: #1E293B;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .card {
                        background: white;
                        padding: 40px;
                        border-radius: 12px;
                        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
                        text-align: center;
                        max-width: 400px;
                    }
                    h1 { color: #10B981; font-size: 22px; margin-bottom: 12px; }
                    p { color: #64748B; font-size: 14px; line-height: 1.5; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>✓ Authentication Successful</h1>
                    <p>EasyQist has been successfully authorized. You can close this tab and return to the application.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            # Ignore favicon or pre-flight requests and keep the server running
            self.send_response(404)
            self.end_headers()

class RobustOAuthServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.auth_code = None

class BackupService:
    @staticmethod
    def get_client_secrets_path() -> str:
        return CLIENT_SECRETS_FILE

    @staticmethod
    def is_google_configured() -> bool:
        """Checks if the client_secrets.json file is present in the application directory."""
        return os.path.exists(CLIENT_SECRETS_FILE)

    @staticmethod
    def get_credentials() -> Optional[Credentials]:
        """Loads valid user credentials from disk, refreshing them if expired."""
        creds = None
        if os.path.exists(TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            except Exception as e:
                print(f"Failed to load google token: {e}")
                return None

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Failed to refresh google token: {e}")
                return None
        return creds

    @staticmethod
    def get_connected_account() -> Optional[str]:
        """Retrieves the email address of the connected Google Account."""
        creds = BackupService.get_credentials()
        if not creds:
            return None
        try:
            # Call the UserInfo API or people API to get email, or just build the drive service
            service = build('drive', 'v3', credentials=creds)
            about = service.about().get(fields="user(emailAddress)").execute()
            return about.get('user', {}).get('emailAddress')
        except Exception as e:
            print(f"Failed to get connected account info: {e}")
            return None

    @staticmethod
    def get_connected_account_details() -> Tuple[Optional[str], Optional[str], Optional[bytes]]:
        """Retrieves the email address, display name, and profile photo bytes of the connected Google Account."""
        creds = BackupService.get_credentials()
        if not creds:
            return None, None, None
        try:
            service = build('drive', 'v3', credentials=creds)
            about = service.about().get(fields="user(emailAddress, displayName, photoLink)").execute()
            user_info = about.get('user', {})
            email = user_info.get('emailAddress')
            display_name = user_info.get('displayName')
            photo_link = user_info.get('photoLink')
            
            photo_bytes = None
            if photo_link:
                try:
                    import urllib.request
                    req = urllib.request.Request(photo_link)
                    if creds and creds.token:
                        req.add_header('Authorization', f'Bearer {creds.token}')
                    with urllib.request.urlopen(req, timeout=5) as response:
                        photo_bytes = response.read()
                except Exception as e:
                    print(f"Failed to download profile photo: {e}")
                    
            return email, display_name, photo_bytes
        except Exception as e:
            print(f"Failed to get connected account details: {e}")
            return None, None, None

    @staticmethod
    def authenticate_google(port: int = 0) -> Tuple[bool, str]:
        """
        Launches the system web browser to perform OAuth 2.0 authorization.
        Saves credentials to google_token.json.
        Returns:
            Tuple[bool, str]: (Success, status_message_or_error)
        """
        if not BackupService.is_google_configured():
            return False, "Google Client Credentials (client_secrets.json) are missing in the application directory."

        try:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            
            # Start the robust server on 127.0.0.1 with an ephemeral port (0)
            server = RobustOAuthServer(('127.0.0.1', port), OAuthCallbackHandler)
            assigned_port = server.server_port
            
            # Set the redirect URI to point to our local server
            flow.redirect_uri = f"http://127.0.0.1:{assigned_port}/"
            
            # Generate authorization URL
            authorization_url, state = flow.authorization_url(
                prompt='consent',
                access_type='offline'
            )
            
            # Open the browser to the auth page
            webbrowser.open(authorization_url)
            
            # Loop handling requests until we receive the authorization code
            while server.auth_code is None:
                server.handle_request()
                
            # Clean up and close the server socket
            server.server_close()
            
            # Exchange code for credentials
            flow.fetch_token(code=server.auth_code)
            creds = flow.credentials
            
            # Save the credentials for subsequent runs
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            
            email = BackupService.get_connected_account()
            return True, email or "Success"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def disconnect_google():
        """Clears saved Google OAuth token credentials."""
        if os.path.exists(TOKEN_FILE):
            try:
                os.remove(TOKEN_FILE)
            except Exception as e:
                print(f"Failed to remove token file: {e}")

    @staticmethod
    def create_database_backup() -> Tuple[str, str]:
        """
        Fetches all primary operational tables from Supabase, serializes them as JSON,
        and packages them into a single compressed ZIP file.
        Returns:
            Tuple[str, str]: (Path to the created ZIP file, filename of the ZIP file)
        """
        db = get_db()
        if not db:
            raise Exception("Database client could not be initialized.")

        tables = ["suppliers", "customers", "devices", "sales", "installments", "payments", "audit_logs"]
        temp_dir = tempfile.mkdtemp()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        zip_filename = f"AMC_Backup_{timestamp}.zip"
        zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for table_name in tables:
                try:
                    res = db.table(table_name).select("*").execute()
                    data = res.data or []
                    
                    # Write to temporary JSON file
                    json_path = os.path.join(temp_dir, f"{table_name}.json")
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, default=str)
                        
                    # Add to ZIP archive
                    zip_file.write(json_path, f"{table_name}.json")
                    
                    # Clean up json file
                    try:
                        os.remove(json_path)
                    except Exception:
                        pass
                except Exception as e:
                    print(f"Failed to back up table {table_name}: {e}")

        # Clean up temp directory
        try:
            os.rmdir(temp_dir)
        except Exception:
            pass

        return zip_path, zip_filename

    @staticmethod
    def upload_backup_to_drive(file_path: str, filename: str, progress_callback=None) -> Tuple[bool, str]:
        """
        Uploads the specified backup ZIP file to the user's Google Drive.
        Ensures a dedicated folder named 'EasyQist Backups' exists.
        Returns:
            Tuple[bool, str]: (Success status, status message or file ID)
        """
        creds = BackupService.get_credentials()
        if not creds:
            return False, "Google Account is not connected or session expired."

        try:
            service = build('drive', 'v3', credentials=creds)

            # 1. Find or create the destination folder
            folder_name = "EasyQist Backups"
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = service.files().list(q=query, spaces='drive', fields="files(id)").execute()
            items = results.get('files', [])

            if items:
                folder_id = items[0]['id']
            else:
                # Create the folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = service.files().create(body=folder_metadata, fields='id').execute()
                folder_id = folder.get('id')

            # 2. Upload the ZIP file
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            media = MediaFileUpload(file_path, mimetype='application/zip', resumable=True)
            
            request = service.files().create(body=file_metadata, media_body=media, fields='id')
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status and progress_callback:
                    # progress is a float between 0.0 and 1.0
                    progress_callback(int(status.progress() * 100))

            file_id = response.get('id')
            
            # Clean up local temporary ZIP file
            try:
                os.remove(file_path)
            except Exception:
                pass

            return True, file_id

        except Exception as e:
            return False, str(e)
