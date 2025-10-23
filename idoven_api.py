# -*- coding: utf-8 -*-
"""
Created on Tue Oct 21 10:11:12 2025

@author: eduar
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Oct 14 11:08:39 2025

@author: edillu
"""

import requests
import time
import json
from typing import Dict, Optional
from pathlib import Path


class IdovenAPIClient:
    """Client for testing Idoven API endpoints."""
   
    def __init__(self, base_url: str = "https://api.staging.idoven.ai",
                 upload_url: str = "https://upload.staging.idoven.ai"):
        self.base_url = base_url
        self.upload_url = upload_url
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0
   
    def authenticate(self, client_id: str, client_secret: str) -> Dict:
        """
        Authenticate using OAuth2 client credentials flow.
       
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
           
        Returns:
            Authentication response containing tokens
        """
        url = f"{self.base_url}/auth/login"
       
        payload = {
            "username": client_id,
            "password": client_secret
        }
       
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
               
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
               
        data = response.json()
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")
       
        # Set token expiration (assuming expires_in is in seconds)
        expires_in = data.get("expires_in", 3600)
        self.token_expires_at = time.time() + expires_in
       
        print(f"✓ Authentication successful")
        print(f"  Access token: {self.access_token[:20]}...")
       
        return data
   
    def refresh_access_token(self, refresh_token: Optional[str] = None) -> Dict:
        """
        Refresh the access token using refresh token.
       
        Args:
            refresh_token: Refresh token (uses stored token if not provided)
           
        Returns:
            New authentication response
        """
        url = f"{self.base_url}/oauth/token"
       
        token = refresh_token or self.refresh_token
        if not token:
            raise ValueError("No refresh token available")
       
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": token
        }
       
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
       
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
       
        data = response.json()
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token", self.refresh_token)
       
        expires_in = data.get("expires_in", 3600)
        self.token_expires_at = time.time() + expires_in
       
        print(f"✓ Token refreshed successfully")
       
        return data
   
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers with current access token."""
        if not self.access_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
       
        # Auto-refresh if token is expired
        if time.time() >= self.token_expires_at and self.refresh_token:
            print("Token expired, refreshing...")
            self.refresh_access_token()
       
        return {
            "Authorization": f"Bearer {self.access_token}"
        }
   
    def upload_ecg(self, file_path: str, patient_id: Optional[str] = None) -> Dict:
        """
        Upload an ECG file for analysis.
       
        Args:
            file_path: Path to the SCP ECG file
            patient_id: Optional patient identifier
           
        Returns:
            Upload response containing analysis_id
        """
        url = f"{self.upload_url}/research/upload"
       
        headers = self._get_auth_headers()
       
        # Prepare multipart form data
        files = {
            'file': (Path(file_path).name, open(file_path, 'rb'), 'application/octet-stream')
        }
       
        data = {
            'file': file_path,
            'model_name': 'hf',
            'model_version': '1',
            'channels_mapping_json': '{"I": "I","II": "II", "V1": "V1", "V2": "V2", "V4": "V4", "V6": "V6"}'
        }
       
        if patient_id:
            data['patient_id'] = patient_id
       
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
       
        result = response.json()
        analysis_id = result.get('analysis_id')
       
        print(f"✓ ECG uploaded successfully")
        print(f"  Analysis ID: {analysis_id}")
       
        return result
   
    def get_analysis_results(self, analysis_id: str) -> Dict:
        """
        Get analysis results as JSON.
       
        Args:
            analysis_id: The analysis ID from upload response
           
        Returns:
            Analysis results in JSON format
        """
        url = f"{self.base_url}/research/analysis/{analysis_id}"
       
        headers = self._get_auth_headers()
       
        response = requests.get(url, headers=headers)
        response.raise_for_status()
       
        result = response.json()
       
        print(f"✓ Analysis results retrieved")
        print(f"  Status: {result.get('status', 'N/A')}")
       
        return result
   
    def get_pdf_report(self, analysis_id: str, output_path: str = "report.pdf") -> str:
        """
        Download PDF report for an analysis.
       
        Args:
            analysis_id: The analysis ID
            output_path: Path to save the PDF file
           
        Returns:
            Path to the downloaded PDF file
        """
        url = f"{self.base_url}/research/analysis/{analysis_id}/download"
       
        headers = self._get_auth_headers()
       
        # Get download link
        params = {"format": "pdf"}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
       
        download_data = response.json()
       
        download_url = download_data.get('download_link')
       
        print(download_data)

        if not download_url:
            raise ValueError("No download URL in response")
       
        # Download the PDF
        pdf_response = requests.get(download_url)
        pdf_response.raise_for_status()
       
        with open(output_path, 'wb') as f:
            f.write(pdf_response.content)
       
        print(f"✓ PDF report downloaded to: {output_path}")
       
        return output_path
   
    def wait_for_analysis(self, analysis_id: str, max_wait: int = 300,
                         poll_interval: int = 5) -> Dict:
        """
        Poll for analysis completion.
       
        Args:
            analysis_id: The analysis ID to monitor
            max_wait: Maximum time to wait in seconds
            poll_interval: Time between polls in seconds
           
        Returns:
            Final analysis results
        """
        print(f"Waiting for analysis {analysis_id} to complete...")
       
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                result = self.get_analysis_results(analysis_id)
                status = result.get('status', '').lower()
               
                if status in ['completed', 'success', 'done']:
                    print(f"✓ Analysis completed!")
                    return result
                elif status in ['failed', 'error']:
                    print(f"✗ Analysis failed")
                    return result
                else:
                    print(f"  Status: {status} - waiting...")
                    time.sleep(poll_interval)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"  Analysis not found yet - waiting...")
                    time.sleep(poll_interval)
                else:
                    raise
       
        raise TimeoutError(f"Analysis did not complete within {max_wait} seconds")


def main():
    """Example usage of the Idoven API client."""
   
    # Initialize client
    client = IdovenAPIClient()
   
    # Configuration - replace with your actual credentials
    CLIENT_ID = "farhad.abtahi@ki.se"
    CLIENT_SECRET = "C3!6LijVFeMj9Xm"
    #ECG_FILE_PATH = "./data/ECG_20081029_105642_191010101010.SCP"
    ECG_FILE_PATH = "./data/anonymized/ECG_20170504_163507_ANON000003.SCP"

    try:
        # Step 1: Authenticate
        print("\n=== Step 1: Authentication ===")
        auth_response = client.authenticate(CLIENT_ID, CLIENT_SECRET)
       
        # Step 2: Upload ECG
        print("\n=== Step 2: Upload ECG ===")
        upload_response = client.upload_ecg(ECG_FILE_PATH, patient_id="TEST_PATIENT_001")
        analysis_id = upload_response.get('analysis_id')
       
        # Step 3: Wait for analysis to complete
        print("\n=== Step 3: Wait for Analysis ===")
        analysis_result = client.wait_for_analysis(analysis_id)
       
        # Step 4: Get detailed results
        print("\n=== Step 4: Get Analysis Results ===")
        results = client.get_analysis_results(analysis_id)
        print(json.dumps(results, indent=2))
       
        # Step 5: Download PDF report
        print("\n=== Step 5: Download PDF Report ===")
        pdf_path = client.get_pdf_report(analysis_id, f"report_{analysis_id}.pdf")
       
        print("\n✓ All tests completed successfully!")
       
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()