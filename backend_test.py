import requests
import sys
import json
from datetime import datetime

class DownloadPortalAPITester:
    def __init__(self, base_url="https://contentcatalog-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

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
        # Create a new submission to reject
        test_submission = {
            "name": "Test Rejection",
            "download_link": "https://example.com/reject-test.zip",
            "type": "software"
        }
        success, response = self.run_test("Create Submission for Rejection", "POST", "submissions", 200, test_submission)
        if success and 'id' in response:
            reject_id = response['id']
            return self.run_test("Reject Submission", "POST", f"admin/submissions/{reject_id}/reject", 200)
        return False

    def test_delete_submission(self):
        """Test deleting a submission"""
        # Create a new submission to delete
        test_submission = {
            "name": "Test Deletion",
            "download_link": "https://example.com/delete-test.zip",
            "type": "movie"
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
        test_submission = {
            "name": "Test Game with Optional Fields",
            "download_link": "https://example.com/test-game-full.zip",
            "type": "game",
            "file_size": "4.5 GB",
            "description": "A test game with file size and description"
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

def main():
    print("🚀 Starting Download Portal API Tests...")
    print(f"Testing against: https://contentcatalog-1.preview.emergentagent.com/api")
    print("=" * 60)

    tester = DownloadPortalAPITester()

    # Run all tests in sequence
    test_methods = [
        tester.test_root_endpoint,
        tester.test_get_downloads_empty,
        tester.test_create_submission,
        tester.test_admin_login_invalid,
        tester.test_admin_login_valid,
        tester.test_get_admin_submissions,
        tester.test_approve_submission,
        tester.test_get_downloads_with_data,
        tester.test_downloads_pagination,
        tester.test_downloads_filtering,
        tester.test_theme_get,
        tester.test_theme_update,
        tester.test_reject_submission,
        tester.test_delete_submission
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