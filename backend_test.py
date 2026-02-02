import requests
import sys
import json
from datetime import datetime

class DownloadPortalAPITester:
    def __init__(self, base_url="https://downloadportal-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.captcha_data = None
        self.submission_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected: {expected_status})"
                try:
                    error_data = response.json()
                    details += f" - {error_data}"
                except:
                    details += f" - {response.text[:100]}"

            self.log_test(name, success, details)
            return success, response.json() if success and response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_get_downloads_empty(self):
        """Test getting downloads when empty"""
        success, response = self.run_test("Get Downloads (Empty)", "GET", "downloads", 200)
        if success:
            expected_fields = ['items', 'total', 'page', 'pages']
            has_fields = all(field in response for field in expected_fields)
            if not has_fields:
                self.log_test("Downloads Response Structure", False, f"Missing fields in response: {response}")
                return False
            self.log_test("Downloads Response Structure", True, "All required fields present")
        return success

    def test_create_submission(self):
        """Test creating a new submission"""
        test_submission = {
            "name": "Test Game Download",
            "download_link": "https://example.com/test-game.zip",
            "type": "game"
        }
        success, response = self.run_test("Create Submission", "POST", "submissions", 200, test_submission)
        if success and 'id' in response:
            self.submission_id = response['id']
            return True
        return False

    def test_admin_login_invalid(self):
        """Test admin login with invalid password"""
        return self.run_test("Admin Login (Invalid)", "POST", "admin/login", 401, {"password": "wrong"})

    def test_admin_login_valid(self):
        """Test admin login with valid password"""
        return self.run_test("Admin Login (Valid)", "POST", "admin/login", 200, {"password": "admin123"})

    def test_get_admin_submissions(self):
        """Test getting admin submissions"""
        success, response = self.run_test("Get Admin Submissions", "GET", "admin/submissions", 200)
        if success:
            expected_fields = ['items', 'total', 'page', 'pages']
            has_fields = all(field in response for field in expected_fields)
            if not has_fields:
                self.log_test("Admin Submissions Response Structure", False, f"Missing fields: {response}")
                return False
            self.log_test("Admin Submissions Response Structure", True, "All required fields present")
        return success

    def test_approve_submission(self):
        """Test approving a submission"""
        if hasattr(self, 'submission_id'):
            return self.run_test("Approve Submission", "POST", f"admin/submissions/{self.submission_id}/approve", 200)
        else:
            self.log_test("Approve Submission", False, "No submission ID available")
            return False

    def test_get_downloads_with_data(self):
        """Test getting downloads after approval"""
        success, response = self.run_test("Get Downloads (With Data)", "GET", "downloads", 200)
        if success and response.get('total', 0) > 0:
            self.log_test("Downloads Contains Data", True, f"Found {response['total']} downloads")
            return True
        elif success:
            self.log_test("Downloads Contains Data", False, "No downloads found after approval")
            return False
        return success

    def test_downloads_pagination(self):
        """Test downloads pagination"""
        return self.run_test("Downloads Pagination", "GET", "downloads?page=1&limit=10", 200)

    def test_downloads_filtering(self):
        """Test downloads type filtering"""
        return self.run_test("Downloads Type Filter", "GET", "downloads?type_filter=game", 200)

    def test_theme_get(self):
        """Test getting theme settings"""
        success, response = self.run_test("Get Theme Settings", "GET", "theme", 200)
        if success:
            expected_fields = ['mode', 'accent_color']
            has_fields = all(field in response for field in expected_fields)
            if not has_fields:
                self.log_test("Theme Response Structure", False, f"Missing fields: {response}")
                return False
            self.log_test("Theme Response Structure", True, "All required fields present")
        return success

    def test_theme_update(self):
        """Test updating theme settings"""
        theme_update = {
            "mode": "light",
            "accent_color": "#FF00FF"
        }
        return self.run_test("Update Theme Settings", "PUT", "theme", 200, theme_update)

    def test_reject_submission(self):
        """Test rejecting a submission (create new one first)"""
        # Get a fresh captcha
        captcha_success, captcha_response = self.run_test("Get Captcha for Rejection Test", "GET", "captcha", 200)
        if not captcha_success:
            return False
        
        # Parse captcha answer
        question = captcha_response['question']
        import re
        match = re.search(r'What is (\d+) ([\+\-×]) (\d+)\?', question)
        if not match:
            return False
        
        num1, operator, num2 = int(match.group(1)), match.group(2), int(match.group(3))
        if operator == '+':
            answer = num1 + num2
        elif operator == '-':
            answer = num1 - num2
        elif operator == '×':
            answer = num1 * num2
        
        # Create a new submission to reject
        test_submission = {
            "name": "Test Rejection",
            "download_link": "https://example.com/reject-test.zip",
            "type": "software",
            "site_name": "RejectSite",
            "site_url": "https://rejectsite.com",
            "captcha_id": captcha_response['id'],
            "captcha_answer": answer
        }
        success, response = self.run_test("Create Submission for Rejection", "POST", "submissions", 200, test_submission)
        if success and 'id' in response:
            reject_id = response['id']
            return self.run_test("Reject Submission", "POST", f"admin/submissions/{reject_id}/reject", 200)
        return False

    def test_delete_submission(self):
        """Test deleting a submission"""
        # Get a fresh captcha
        captcha_success, captcha_response = self.run_test("Get Captcha for Deletion Test", "GET", "captcha", 200)
        if not captcha_success:
            return False
        
        # Parse captcha answer
        question = captcha_response['question']
        import re
        match = re.search(r'What is (\d+) ([\+\-×]) (\d+)\?', question)
        if not match:
            return False
        
        num1, operator, num2 = int(match.group(1)), match.group(2), int(match.group(3))
        if operator == '+':
            answer = num1 + num2
        elif operator == '-':
            answer = num1 - num2
        elif operator == '×':
            answer = num1 * num2
        
        # Create a new submission to delete
        test_submission = {
            "name": "Test Deletion",
            "download_link": "https://example.com/delete-test.zip",
            "type": "movie",
            "site_name": "DeleteSite",
            "site_url": "https://deletesite.com",
            "captcha_id": captcha_response['id'],
            "captcha_answer": answer
        }
        success, response = self.run_test("Create Submission for Deletion", "POST", "submissions", 200, test_submission)
        if success and 'id' in response:
            delete_id = response['id']
            return self.run_test("Delete Submission", "DELETE", f"admin/submissions/{delete_id}", 200)
        return False

    def test_get_stats(self):
        """Test getting database statistics"""
        success, response = self.run_test("Get Database Stats", "GET", "stats", 200)
        if success:
            expected_fields = ['total', 'by_type', 'top_downloads']
            has_fields = all(field in response for field in expected_fields)
            if not has_fields:
                self.log_test("Stats Response Structure", False, f"Missing fields: {response}")
                return False
            
            # Check by_type structure
            by_type = response.get('by_type', {})
            expected_types = ['game', 'software', 'movie', 'tv_show']
            has_types = all(t in by_type for t in expected_types)
            if not has_types:
                self.log_test("Stats By Type Structure", False, f"Missing types: {by_type}")
                return False
            
            self.log_test("Stats Response Structure", True, f"Total: {response['total']}, Types: {by_type}")
        return success

    def test_search_functionality(self):
        """Test search functionality"""
        # Test search with a common term
        success, response = self.run_test("Search Downloads", "GET", "downloads?search=test", 200)
        if success:
            self.log_test("Search Functionality", True, f"Search returned {response.get('total', 0)} results")
        return success

    def test_download_increment(self):
        """Test download counter increment"""
        # First get a download to increment
        success, response = self.run_test("Get Downloads for Increment", "GET", "downloads?limit=1", 200)
        if success and response.get('items'):
            download_id = response['items'][0]['id']
            original_count = response['items'][0].get('download_count', 0)
            
            # Increment the download count
            increment_success, _ = self.run_test("Increment Download Count", "POST", f"downloads/{download_id}/increment", 200)
            
            if increment_success:
                # Verify the count increased
                verify_success, verify_response = self.run_test("Verify Increment", "GET", f"downloads?limit=50", 200)
                if verify_success:
                    # Find the same download and check if count increased
                    updated_download = next((d for d in verify_response['items'] if d['id'] == download_id), None)
                    if updated_download and updated_download.get('download_count', 0) > original_count:
                        self.log_test("Download Count Verification", True, f"Count increased from {original_count} to {updated_download['download_count']}")
                        return True
                    else:
                        self.log_test("Download Count Verification", False, "Count did not increase")
                        return False
            return increment_success
        else:
            self.log_test("Download Increment", False, "No downloads available to increment")
            return False

    def test_admin_seed_database(self):
        """Test admin database seeding"""
        return self.run_test("Seed Database", "POST", "admin/seed", 200)

    def test_downloads_with_optional_fields(self):
        """Test creating submission with optional fields"""
        # Get a fresh captcha
        captcha_success, captcha_response = self.run_test("Get Captcha for Optional Fields Test", "GET", "captcha", 200)
        if not captcha_success:
            return False
        
        # Parse captcha answer
        question = captcha_response['question']
        import re
        match = re.search(r'What is (\d+) ([\+\-×]) (\d+)\?', question)
        if not match:
            return False
        
        num1, operator, num2 = int(match.group(1)), match.group(2), int(match.group(3))
        if operator == '+':
            answer = num1 + num2
        elif operator == '-':
            answer = num1 - num2
        elif operator == '×':
            answer = num1 * num2
        
        test_submission = {
            "name": "Test Game with Optional Fields",
            "download_link": "https://example.com/test-game-full.zip",
            "type": "game",
            "site_name": "OptionalSite",
            "site_url": "https://optionalsite.com",
            "file_size": "4.5 GB",
            "description": "A test game with file size and description",
            "captcha_id": captcha_response['id'],
            "captcha_answer": answer
        }
        success, response = self.run_test("Create Submission with Optional Fields", "POST", "submissions", 200, test_submission)
        if success:
            # Verify the optional fields are included
            if response.get('file_size') == "4.5 GB" and response.get('description'):
                self.log_test("Optional Fields Verification", True, "File size and description saved correctly")
                return True
            else:
                self.log_test("Optional Fields Verification", False, f"Optional fields not saved: {response}")
                return False
        return success

    # ===== NEW TESTS FOR SITE FIELDS AND RECAPTCHA =====

    def test_captcha_generation(self):
        """Test /api/captcha returns a captcha"""
        success, response = self.run_test("Generate Captcha", "GET", "captcha", 200)
        if success:
            required_fields = ['id', 'question']
            has_fields = all(field in response for field in required_fields)
            if has_fields:
                self.captcha_data = response
                self.log_test("Captcha Structure", True, f"Captcha generated: {response['question']}")
                return True
            else:
                self.log_test("Captcha Structure", False, f"Missing fields in captcha response: {response}")
                return False
        return success

    def test_submission_with_site_fields(self):
        """Test creating submission with required site fields and math captcha"""
        # First ensure reCAPTCHA is disabled
        disable_settings = {
            "recaptcha_enable_submit": False,
            "recaptcha_enable_auth": False
        }
        self.run_test("Ensure reCAPTCHA Disabled", "PUT", "admin/settings", 200, disable_settings)
        
        # Get a fresh captcha
        captcha_success, captcha_response = self.run_test("Get Fresh Captcha for Submission", "GET", "captcha", 200)
        if not captcha_success:
            return False
        
        # Parse the math question to get the answer
        question = captcha_response['question']
        # Extract numbers and operator from question like "What is 5 + 3?"
        import re
        match = re.search(r'What is (\d+) ([\+\-×]) (\d+)\?', question)
        if not match:
            self.log_test("Parse Captcha Question", False, f"Could not parse question: {question}")
            return False
        
        num1, operator, num2 = int(match.group(1)), match.group(2), int(match.group(3))
        if operator == '+':
            answer = num1 + num2
        elif operator == '-':
            answer = num1 - num2
        elif operator == '×':
            answer = num1 * num2
        
        test_submission = {
            "name": "Epic Adventure Game",
            "download_link": "https://example.com/epic-adventure.zip",
            "type": "game",
            "site_name": "GameHub",
            "site_url": "https://gamehub.com",
            "file_size": "2.5 GB",
            "description": "An epic adventure game",
            "captcha_id": captcha_response['id'],
            "captcha_answer": answer
        }
        
        success, response = self.run_test("Create Submission with Site Fields", "POST", "submissions", 200, test_submission)
        if success:
            # Verify site fields are in response
            if response.get('site_name') == "GameHub" and response.get('site_url') == "https://gamehub.com":
                self.submission_id = response['id']
                self.log_test("Site Fields in Submission", True, f"Site fields saved: {response.get('site_name')}, {response.get('site_url')}")
                return True
            else:
                self.log_test("Site Fields in Submission", False, f"Site fields missing or incorrect: {response}")
                return False
        return success

    def test_approve_submission_with_site_fields(self):
        """Test approving submission and verify download includes site fields"""
        if not self.submission_id:
            self.log_test("Approve Submission with Site Fields", False, "No submission ID available")
            return False
        
        # Approve the submission
        approve_success, _ = self.run_test("Approve Submission with Site Fields", "POST", f"admin/submissions/{self.submission_id}/approve", 200)
        if not approve_success:
            return False
        
        # Get downloads and verify site fields are present
        success, response = self.run_test("Verify Site Fields in Downloads", "GET", "downloads", 200)
        if success and response.get('items'):
            # Find our approved download
            approved_download = None
            for download in response['items']:
                if download.get('site_name') == "GameHub":
                    approved_download = download
                    break
            
            if approved_download:
                if approved_download.get('site_name') == "GameHub" and approved_download.get('site_url') == "https://gamehub.com":
                    self.log_test("Site Fields in Download", True, f"Download contains site fields: {approved_download.get('site_name')}, {approved_download.get('site_url')}")
                    return True
                else:
                    self.log_test("Site Fields in Download", False, f"Site fields missing in download: {approved_download}")
                    return False
            else:
                self.log_test("Site Fields in Download", False, "Could not find approved download with site fields")
                return False
        return success

    def test_site_url_validation(self):
        """Test that submission with invalid site_url is rejected"""
        # Get a captcha first
        captcha_success, captcha_response = self.run_test("Get Captcha for URL Validation", "GET", "captcha", 200)
        if not captcha_success:
            return False
        
        # Parse captcha answer
        question = captcha_response['question']
        import re
        match = re.search(r'What is (\d+) ([\+\-×]) (\d+)\?', question)
        if not match:
            return False
        
        num1, operator, num2 = int(match.group(1)), match.group(2), int(match.group(3))
        if operator == '+':
            answer = num1 + num2
        elif operator == '-':
            answer = num1 - num2
        elif operator == '×':
            answer = num1 * num2
        
        # Test with invalid URL (missing http/https)
        invalid_submission = {
            "name": "Test Invalid URL",
            "download_link": "https://example.com/test.zip",
            "type": "game",
            "site_name": "TestSite",
            "site_url": "invalid-url.com",  # Missing http/https
            "captcha_id": captcha_response['id'],
            "captcha_answer": answer
        }
        
        # This should fail with 400 status
        success, response = self.run_test("Invalid Site URL Validation", "POST", "submissions", 400, invalid_submission)
        return success

    def test_recaptcha_settings_public(self):
        """Test /api/recaptcha/settings returns only site_key + toggles (no secret)"""
        success, response = self.run_test("Get reCAPTCHA Settings Public", "GET", "recaptcha/settings", 200)
        if success:
            expected_fields = ['site_key', 'enable_submit', 'enable_auth']
            has_fields = all(field in response for field in expected_fields)
            has_secret = 'secret_key' in response or 'recaptcha_secret_key' in response
            
            if has_fields and not has_secret:
                self.log_test("reCAPTCHA Settings Structure", True, f"Public settings correct: {list(response.keys())}")
                return True
            else:
                self.log_test("reCAPTCHA Settings Structure", False, f"Invalid structure or secret exposed: {response}")
                return False
        return success

    def test_site_settings_no_secret(self):
        """Test /api/settings never returns recaptcha_secret_key"""
        success, response = self.run_test("Get Site Settings", "GET", "settings", 200)
        if success:
            # Check that recaptcha_secret_key is None or not present
            secret_key = response.get('recaptcha_secret_key')
            if secret_key is None:
                self.log_test("Site Settings Secret Key Hidden", True, "recaptcha_secret_key is properly hidden (None)")
                return True
            else:
                self.log_test("Site Settings Secret Key Hidden", False, f"recaptcha_secret_key exposed: {secret_key}")
                return False
        return success

    def test_admin_settings_recaptcha_validation(self):
        """Test admin settings update: enabling recaptcha without keys fails, with keys succeeds"""
        
        # Test 1: Try to enable reCAPTCHA without keys (should fail)
        invalid_settings = {
            "recaptcha_enable_submit": True,
            "recaptcha_site_key": "",
            "recaptcha_secret_key": ""
        }
        
        fail_success, _ = self.run_test("Enable reCAPTCHA Without Keys", "PUT", "admin/settings", 400, invalid_settings)
        
        # Test 2: Enable reCAPTCHA with keys (should succeed)
        valid_settings = {
            "recaptcha_enable_submit": True,
            "recaptcha_site_key": "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",  # Test key
            "recaptcha_secret_key": "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"  # Test secret
        }
        
        success_success, _ = self.run_test("Enable reCAPTCHA With Keys", "PUT", "admin/settings", 200, valid_settings)
        
        return fail_success and success_success

    def test_recaptcha_submission_validation(self):
        """Test that when reCAPTCHA is enabled, submissions without token are rejected"""
        
        # First ensure reCAPTCHA is enabled for submissions
        enable_settings = {
            "recaptcha_enable_submit": True,
            "recaptcha_site_key": "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
            "recaptcha_secret_key": "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
        }
        
        setup_success, _ = self.run_test("Setup reCAPTCHA for Testing", "PUT", "admin/settings", 200, enable_settings)
        if not setup_success:
            return False
        
        # Try to submit without reCAPTCHA token (should fail)
        submission_without_token = {
            "name": "Test reCAPTCHA Validation",
            "download_link": "https://example.com/test.zip",
            "type": "game",
            "site_name": "TestSite",
            "site_url": "https://testsite.com"
            # No recaptcha_token provided
        }
        
        # This should fail with 400 and "Invalid reCAPTCHA" message
        success, response = self.run_test("Submission Without reCAPTCHA Token", "POST", "submissions", 400, submission_without_token)
        
        # Disable reCAPTCHA for other tests
        disable_settings = {
            "recaptcha_enable_submit": False,
            "recaptcha_enable_auth": False
        }
        self.run_test("Disable reCAPTCHA After Testing", "PUT", "admin/settings", 200, disable_settings)
        
        return success

    def test_recaptcha_auth_validation(self):
        """Test that when reCAPTCHA is enabled for auth, registration without token is rejected"""
        
        # Enable reCAPTCHA for auth
        enable_settings = {
            "recaptcha_enable_auth": True,
            "recaptcha_site_key": "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
            "recaptcha_secret_key": "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
        }
        
        setup_success, _ = self.run_test("Setup reCAPTCHA for Auth Testing", "PUT", "admin/settings", 200, enable_settings)
        if not setup_success:
            return False
        
        # Try to register without reCAPTCHA token (should fail)
        registration_without_token = {
            "email": "test@example.com",
            "password": "testpassword123"
            # No recaptcha_token provided
        }
        
        success, response = self.run_test("Registration Without reCAPTCHA Token", "POST", "auth/register", 400, registration_without_token)
        
        # Disable reCAPTCHA for other tests
        disable_settings = {
            "recaptcha_enable_submit": False,
            "recaptcha_enable_auth": False
        }
        self.run_test("Disable reCAPTCHA After Auth Testing", "PUT", "admin/settings", 200, disable_settings)
        
        return success

    def test_site_name_length_validation(self):
        """Test that site_name with more than 15 characters is rejected"""
        # Get a captcha first
        captcha_success, captcha_response = self.run_test("Get Captcha for Site Name Validation", "GET", "captcha", 200)
        if not captcha_success:
            return False
        
        # Parse captcha answer
        question = captcha_response['question']
        import re
        match = re.search(r'What is (\d+) ([\+\-×]) (\d+)\?', question)
        if not match:
            return False
        
        num1, operator, num2 = int(match.group(1)), match.group(2), int(match.group(3))
        if operator == '+':
            answer = num1 + num2
        elif operator == '-':
            answer = num1 - num2
        elif operator == '×':
            answer = num1 * num2
        
        # Test with site_name longer than 15 characters
        invalid_submission = {
            "name": "Test Long Site Name",
            "download_link": "https://example.com/test.zip",
            "type": "game",
            "site_name": "ThisSiteNameIsTooLongForValidation",  # 34 characters > 15
            "site_url": "https://example.com",
            "captcha_id": captcha_response['id'],
            "captcha_answer": answer
        }
        
        # This should fail with 422 status (validation error)
        success, response = self.run_test("Long Site Name Validation", "POST", "submissions", 422, invalid_submission)
        return success

def main():
    print("🚀 Starting Download Portal API Tests...")
    print(f"Testing against: https://downloadportal-1.preview.emergentagent.com/api")
    print("=" * 60)

    tester = DownloadPortalAPITester()

    # Run all tests in sequence
    test_methods = [
        # Original tests
        tester.test_root_endpoint,
        tester.test_get_downloads_empty,
        
        # New comprehensive site fields and reCAPTCHA tests
        tester.test_captcha_generation,
        tester.test_submission_with_site_fields,
        tester.test_approve_submission_with_site_fields,
        tester.test_site_url_validation,
        tester.test_site_name_length_validation,
        tester.test_recaptcha_settings_public,
        tester.test_site_settings_no_secret,
        tester.test_admin_settings_recaptcha_validation,
        tester.test_recaptcha_submission_validation,
        tester.test_recaptcha_auth_validation,
        
        # Admin and other functionality tests
        tester.test_admin_login_invalid,
        tester.test_admin_login_valid,
        tester.test_get_admin_submissions,
        tester.test_downloads_pagination,
        tester.test_downloads_filtering,
        tester.test_theme_get,
        tester.test_theme_update,
        tester.test_reject_submission,
        tester.test_delete_submission,
        tester.test_get_stats,
        tester.test_search_functionality,
        tester.test_download_increment,
        tester.test_downloads_with_optional_fields
    ]

    for test_method in test_methods:
        test_method()
        print()  # Add spacing between tests

    # Print summary
    print("=" * 60)
    print(f"📊 TEST SUMMARY")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    # Print failed tests
    failed_tests = [result for result in tester.test_results if not result['success']]
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"  - {test['test']}: {test['details']}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())