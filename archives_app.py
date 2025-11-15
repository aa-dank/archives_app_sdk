import httpx
from urllib import parse
import os

APP_URL = r"ppdo-prod-app-1.vm.aws.ucsc.edu"
APP_USERNAME = ""
APP_PASSWORD = ""

# For local testing
# APP_URL = r"127.0.0.1:5000"

#attempt to use dotenv for loading env vars
try:
    from dotenv import load_dotenv
    load_dotenv()
    APP_URL = os.getenv('APP_URL', APP_URL)
    APP_PASSWORD = os.getenv('APP_PASSWORD', APP_PASSWORD)
    APP_USERNAME = os.getenv('APP_USERNAME', APP_USERNAME)
except ImportError:
    pass



class ArchivesApp:

    def __init__(self, username, password, app_url=None):
        self.username = username
        self.password = password
        self.app_url = app_url or APP_URL
        
        # Determine protocol based on app_url
        protocol = "https://" if not self.app_url.startswith(("http://", "https://")) else ""
        base_url = f"{protocol}{self.app_url}"
        
        self.edit_url_template = f"{base_url}/api/server_change?edit_type={{}}&old_path={{}}&new_path={{}}"
        self.request_headers = {'user': self.username, 'password': self.password}
        self.consolidation_url_template = f"{base_url}/api/consolidate_dirs?asset_path={{}}&destination_path={{}}"
        self.archiving_url_template = f"{base_url}/api/upload_file"
        self.project_location_url_template = f"{base_url}/api/project_location"
        self.file_locations_url_template = f"{base_url}/api/archived_or_not"

    def enqueue_move_edit(self, target_path, destination_path):
        new_path = parse.quote(destination_path)
        old_path = parse.quote(target_path)
        move_url = self.edit_url_template.format('MOVE', old_path, new_path)
        move_response = httpx.get(url=move_url,
                                     headers= self.request_headers,
                                     verify=False)
        return move_response
    
    def enqueue_delete_edit(self, target_path):
        old_path = parse.quote(target_path)
        delete_url = self.edit_url_template.format('DELETE', old_path, '')
        delete_response = httpx.get(url=delete_url,
                                       headers= self.request_headers,
                                       verify=False)
        return delete_response
    
    def enqueue_consolidation(self, asset_path, destination_path):
        asset_path = parse.quote(asset_path)
        destination_path = parse.quote(destination_path)
        consolidate_url = self.consolidation_url_template.format(asset_path, destination_path)
        consolidate_response = httpx.get(url=consolidate_url,
                                            headers= self.request_headers,
                                            verify=False)
        return consolidate_response
    
    def enqueue_create_edit(self, destination_path):
        new_path = parse.quote(destination_path)
        create_url = self.edit_url_template.format('CREATE', '', new_path)
        create_response = httpx.get(url=create_url,
                                       headers= self.request_headers,
                                       verify=False)
        return create_response
    
    def enqueue_rename_edit(self, target_path, destination_path):
        new_path = parse.quote(destination_path)
        old_path = parse.quote(target_path)
        rename_url = self.edit_url_template.format('RENAME', old_path, new_path)
        rename_response = httpx.get(url=rename_url,
                                        headers= self.request_headers,
                                        verify=False)
        return rename_response
    
    def enqueue_archiving(self, target_path, destination_path = None, filing_code= None, project_num = None, document_date: str = None):
        """
        Upload a file for archiving with the associated metadata.
        
        Args:
            target_path (str): The path to the file to be archived
            destination_path (str): The destination path for the archived file. If provided, may override project_number and filing_code on the server.
            filing_code (str): The filing code for categorization (sent as destination_directory).
            project_num (str): The project number associated with the file.
            document_date (str, optional): The date associated with the document (format: 'YYYY-MM-DD').
            
        Returns:
            Response: The response from the upload file API
        """
        
        # Prepare the filename from the target path
        filename = os.path.basename(target_path)
        
        # requires either destination_path or both filing_code and project_num
        if not destination_path and (not filing_code or not project_num):
            raise ValueError("Either destination_path or both filing_code and project_num must be provided.")


        # Open the file to be uploaded
        with open(target_path, 'rb') as file_to_upload:
            files = {'file': (filename, file_to_upload)}
            form_data = {
                'project_number': project_num,
                'destination_directory': filing_code,
                'destination_path': destination_path,
                'notes': f"Automatically archived from {target_path}"
            }
            if document_date:
                form_data['document_date'] = document_date
            
            # Send the POST request
            response = httpx.post(
                url=self.archiving_url_template,
                files=files,
                data=form_data,
                headers=self.request_headers, # Keep auth in headers
                verify=False
            )
            
        return response
    
    def get_project_location(self, project_number):
        """
        Get the project location for a given project number.
        
        Args:
            project_number (str): The project number to look up.
            
        Returns:
            Response: The response from the project location API containing project details and file server location.
        """
        
        # Prepare the URL with project number as query parameter
        url = f"{self.project_location_url_template}?project={parse.quote(str(project_number))}"
        
        # Send the GET request
        response = httpx.get(
            url=url,
            headers=self.request_headers,
            verify=False
        )
        
        return response
    
    def file_locations(self, filepath):
        """
        Check if a file exists on the server and return its locations.
        
        Args:
            filepath (str): The path to the file to check.
            
        Returns:
            Response: The response from the archived_or_not API containing file locations.
        """
        
        # Prepare the filename from the filepath
        filename = os.path.basename(filepath)
        
        # Open the file and send it to the server endpoint
        with open(filepath, 'rb') as file_to_check:
            files = {'file': (filename, file_to_check)}
            
            # Send the POST request
            response = httpx.post(
                url=self.file_locations_url_template,
                files=files,
                headers=self.request_headers,
                verify=False
            )
            
        return response
