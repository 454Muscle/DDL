#!/usr/bin/env python3
"""
Focused test script for the specific review request items:
1) GET /api/settings returns new branding/footer fields and still hides resend_api_key + recaptcha_secret_key.
2) PUT /api/admin/settings updates site_name, typography fields, footer templates.
3) GET /api/admin/downloads?search=... returns PaginatedDownloads with items.
4) DELETE /api/admin/downloads/{id} deletes an approved download and subsequent search no longer returns it.
5) Bulk submissions endpoint still works and respects daily limit.
"""

import requests
import json
import sys
from datetime import datetime

class ReviewRequestTester:
    def __init__(self, base_url="https://downloadportal-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_download_id = None

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
                    details += f" - {response.text[:200]}"

            self.log_test(name, success, details)
            return success, response.json() if success and response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_1_get_settings_branding_footer_fields(self):
        """Test 1: GET /api/settings returns new branding/footer fields and hides secret keys"""
        print("\n=== TEST 1: GET /api/settings branding/footer fields ===")
        
        success, response = self.run_test("GET /api/settings", "GET", "settings", 200)
        if not success:
            return False

        # Check for new branding fields
        branding_fields = [
            'site_name', 'site_name_font_family', 'site_name_font_weight', 
            'site_name_font_color', 'body_font_family', 'body_font_weight'
        ]
        
        # Check for footer fields
        footer_fields = [
            'footer_enabled', 'footer_line1_template', 'footer_line2_template'
        ]
        
        # Check that secret keys are hidden
        secret_keys = ['resend_api_key', 'recaptcha_secret_key']
        
        missing_branding = [field for field in branding_fields if field not in response]
        missing_footer = [field for field in footer_fields if field not in response]
        exposed_secrets = [key for key in secret_keys if response.get(key) is not None]
        
        if missing_branding:
            self.log_test("Branding Fields Present", False, f"Missing branding fields: {missing_branding}")
            return False
        
        if missing_footer:
            self.log_test("Footer Fields Present", False, f"Missing footer fields: {missing_footer}")
            return False
            
        if exposed_secrets:
            self.log_test("Secret Keys Hidden", False, f"Exposed secret keys: {exposed_secrets}")
            return False
        
        self.log_test("Branding Fields Present", True, f"All branding fields found: {branding_fields}")
        self.log_test("Footer Fields Present", True, f"All footer fields found: {footer_fields}")
        self.log_test("Secret Keys Hidden", True, "resend_api_key and recaptcha_secret_key properly hidden")
        
        return True

    def test_2_put_admin_settings_updates(self):
        """Test 2: PUT /api/admin/settings updates site_name, typography fields, footer templates"""
        print("\n=== TEST 2: PUT /api/admin/settings updates ===")
        
        # Test data for updating settings
        update_data = {
            "site_name": "TEST PORTAL",
            "site_name_font_family": "Arial",
            "site_name_font_weight": "600",
            "site_name_font_color": "#FF0000",
            "body_font_family": "Helvetica",
            "body_font_weight": "300",
            "footer_enabled": True,
            "footer_line1_template": "Contact us at {admin_email} for support.",
            "footer_line2_template": "© {year} {site_name}. All rights reserved."
        }
        
        success, response = self.run_test("PUT /api/admin/settings", "PUT", "admin/settings", 200, update_data)
        if not success:
            return False
        
        # Verify the updates were applied
        get_success, get_response = self.run_test("GET /api/settings after update", "GET", "settings", 200)
        if not get_success:
            return False
        
        # Check each updated field
        verification_results = []
        for key, expected_value in update_data.items():
            actual_value = get_response.get(key)
            if actual_value == expected_value:
                verification_results.append(f"✓ {key}: {actual_value}")
            else:
                verification_results.append(f"✗ {key}: expected {expected_value}, got {actual_value}")
                self.log_test(f"Update Verification - {key}", False, f"Expected {expected_value}, got {actual_value}")
                return False
        
        self.log_test("Settings Update Verification", True, f"All fields updated correctly: {len(verification_results)} fields")
        return True

    def test_3_get_admin_downloads_search(self):
        """Test 3: GET /api/admin/downloads?search=... returns PaginatedDownloads with items"""
        print("\n=== TEST 3: GET /api/admin/downloads search ===")
        
        # First, ensure we have some data by seeding the database
        seed_success, _ = self.run_test("Seed database for search test", "POST", "admin/seed", 200)
        if not seed_success:
            print("Warning: Database seeding failed, continuing with existing data...")
        
        # Test search without query (should return all approved downloads)
        success, response = self.run_test("GET /api/admin/downloads (no search)", "GET", "admin/downloads", 200)
        if not success:
            return False
        
        # Verify PaginatedDownloads structure
        required_fields = ['items', 'total', 'page', 'pages']
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            self.log_test("PaginatedDownloads Structure", False, f"Missing fields: {missing_fields}")
            return False
        
        self.log_test("PaginatedDownloads Structure", True, f"All required fields present: {required_fields}")
        
        total_items = response.get('total', 0)
        if total_items == 0:
            self.log_test("Downloads Available", False, "No downloads found for search testing")
            return False
        
        self.log_test("Downloads Available", True, f"Found {total_items} downloads")
        
        # Test search with a query
        search_success, search_response = self.run_test("GET /api/admin/downloads?search=game", "GET", "admin/downloads?search=game", 200)
        if not search_success:
            return False
        
        # Verify search results structure
        search_missing_fields = [field for field in required_fields if field not in search_response]
        if search_missing_fields:
            self.log_test("Search Results Structure", False, f"Missing fields in search: {search_missing_fields}")
            return False
        
        search_total = search_response.get('total', 0)
        self.log_test("Search Functionality", True, f"Search for 'game' returned {search_total} results")
        
        # Store a download ID for deletion test
        if search_response.get('items'):
            self.created_download_id = search_response['items'][0]['id']
            self.log_test("Download ID for Deletion Test", True, f"Stored download ID: {self.created_download_id}")
        
        return True

    def test_4_delete_admin_download(self):
        """Test 4: DELETE /api/admin/downloads/{id} deletes download and search no longer returns it"""
        print("\n=== TEST 4: DELETE /api/admin/downloads/{id} ===")
        
        if not self.created_download_id:
            self.log_test("Delete Download Test", False, "No download ID available for deletion test")
            return False
        
        # Get initial count
        initial_success, initial_response = self.run_test("Get initial download count", "GET", "admin/downloads", 200)
        if not initial_success:
            return False
        
        initial_total = initial_response.get('total', 0)
        
        # Delete the download
        delete_success, delete_response = self.run_test(f"DELETE /api/admin/downloads/{self.created_download_id}", "DELETE", f"admin/downloads/{self.created_download_id}", 200)
        if not delete_success:
            return False
        
        # Verify deletion response
        if delete_response.get('success') != True:
            self.log_test("Delete Response Verification", False, f"Expected success:true, got: {delete_response}")
            return False
        
        self.log_test("Delete Response Verification", True, "Delete response contains success:true")
        
        # Verify the download is no longer in search results
        after_success, after_response = self.run_test("Get downloads after deletion", "GET", "admin/downloads", 200)
        if not after_success:
            return False
        
        after_total = after_response.get('total', 0)
        
        if after_total != initial_total - 1:
            self.log_test("Download Count After Deletion", False, f"Expected {initial_total - 1}, got {after_total}")
            return False
        
        self.log_test("Download Count After Deletion", True, f"Count decreased from {initial_total} to {after_total}")
        
        # Verify the specific download is not in the results
        deleted_download_found = any(item['id'] == self.created_download_id for item in after_response.get('items', []))
        
        if deleted_download_found:
            self.log_test("Deleted Download Not Found", False, "Deleted download still appears in search results")
            return False
        
        self.log_test("Deleted Download Not Found", True, "Deleted download no longer appears in search results")
        return True

    def test_5_bulk_submissions_daily_limit(self):
        """Test 5: Bulk submissions endpoint still works and respects daily limit"""
        print("\n=== TEST 5: Bulk submissions with daily limit ===")
        
        # First, check current rate limit
        remaining_success, remaining_response = self.run_test("Check current rate limit", "GET", "submissions/remaining", 200)
        if not remaining_success:
            return False
        
        initial_used = remaining_response.get('used', 0)
        daily_limit = remaining_response.get('daily_limit', 10)
        remaining = remaining_response.get('remaining', 0)
        
        self.log_test("Rate Limit Check", True, f"Used: {initial_used}, Limit: {daily_limit}, Remaining: {remaining}")
        
        # Ensure reCAPTCHA is disabled for this test
        disable_settings = {
            "recaptcha_enable_submit": False,
            "recaptcha_enable_auth": False
        }
        self.run_test("Disable reCAPTCHA for bulk test", "PUT", "admin/settings", 200, disable_settings)
        
        # Get a fresh captcha
        captcha_success, captcha_response = self.run_test("Get captcha for bulk submission", "GET", "captcha", 200)
        if not captcha_success:
            return False
        
        # Parse captcha answer
        question = captcha_response['question']
        import re
        match = re.search(r'What is (\d+) ([\+\-×]) (\d+)\?', question)
        if not match:
            self.log_test("Parse Captcha", False, f"Could not parse question: {question}")
            return False
        
        num1, operator, num2 = int(match.group(1)), match.group(2), int(match.group(3))
        if operator == '+':
            answer = num1 + num2
        elif operator == '-':
            answer = num1 - num2
        elif operator == '×':
            answer = num1 * num2
        
        # Create bulk submission with 2 items (should be within limit)
        items_count = min(2, remaining)  # Don't exceed remaining limit
        
        if items_count <= 0:
            self.log_test("Bulk Submission Test", False, f"No remaining submissions available (used: {initial_used}, limit: {daily_limit})")
            return False
        
        bulk_submission = {
            "items": [
                {
                    "name": f"Bulk Test Game {i+1}",
                    "download_link": f"https://example.com/bulk-test-{i+1}.zip",
                    "type": "game",
                    "site_name": f"BulkSite{i+1}",
                    "site_url": f"https://bulksite{i+1}.com",
                    "file_size": "1.0 GB"
                } for i in range(items_count)
            ],
            "submitter_email": "bulktest@example.com",
            "captcha_id": captcha_response['id'],
            "captcha_answer": answer
        }
        
        # Submit bulk request
        bulk_success, bulk_response = self.run_test("POST /api/submissions/bulk", "POST", "submissions/bulk", 200, bulk_submission)
        if not bulk_success:
            return False
        
        # Verify bulk response structure
        if bulk_response.get('success') != True or bulk_response.get('count') != items_count:
            self.log_test("Bulk Response Structure", False, f"Expected success:true, count:{items_count}, got: {bulk_response}")
            return False
        
        self.log_test("Bulk Response Structure", True, f"Bulk submission successful: {bulk_response}")
        
        # Verify rate limit was updated correctly
        after_success, after_response = self.run_test("Check rate limit after bulk", "GET", "submissions/remaining", 200)
        if not after_success:
            return False
        
        final_used = after_response.get('used', 0)
        expected_used = initial_used + items_count
        
        if final_used != expected_used:
            self.log_test("Rate Limit Update", False, f"Expected used: {expected_used}, got: {final_used}")
            return False
        
        self.log_test("Rate Limit Update", True, f"Rate limit correctly updated from {initial_used} to {final_used}")
        
        # Test that exceeding daily limit is properly rejected
        if final_used < daily_limit:
            # Try to submit more than remaining
            remaining_after = daily_limit - final_used
            excess_items = remaining_after + 1
            
            # Get another captcha
            excess_captcha_success, excess_captcha_response = self.run_test("Get captcha for excess test", "GET", "captcha", 200)
            if excess_captcha_success:
                # Parse captcha
                question = excess_captcha_response['question']
                match = re.search(r'What is (\d+) ([\+\-×]) (\d+)\?', question)
                if match:
                    num1, operator, num2 = int(match.group(1)), match.group(2), int(match.group(3))
                    if operator == '+':
                        answer = num1 + num2
                    elif operator == '-':
                        answer = num1 - num2
                    elif operator == '×':
                        answer = num1 * num2
                    
                    excess_submission = {
                        "items": [
                            {
                                "name": f"Excess Test {i+1}",
                                "download_link": f"https://example.com/excess-{i+1}.zip",
                                "type": "software",
                                "site_name": f"ExcessSite{i+1}",
                                "site_url": f"https://excesssite{i+1}.com"
                            } for i in range(excess_items)
                        ],
                        "submitter_email": "excess@example.com",
                        "captcha_id": excess_captcha_response['id'],
                        "captcha_answer": answer
                    }
                    
                    # This should fail with 429 (rate limit exceeded)
                    excess_success, excess_response = self.run_test("Bulk submission exceeding limit", "POST", "submissions/bulk", 429, excess_submission)
                    if excess_success:
                        self.log_test("Daily Limit Enforcement", True, "Bulk submission properly rejected when exceeding daily limit")
                    else:
                        self.log_test("Daily Limit Enforcement", False, "Bulk submission should have been rejected for exceeding daily limit")
                        return False
        
        return True

    def run_all_tests(self):
        """Run all review request tests"""
        print("🚀 Starting Review Request Specific Tests...")
        print(f"Testing against: {self.base_url}")
        print("=" * 80)
        
        # Run tests in order
        test_methods = [
            self.test_1_get_settings_branding_footer_fields,
            self.test_2_put_admin_settings_updates,
            self.test_3_get_admin_downloads_search,
            self.test_4_delete_admin_download,
            self.test_5_bulk_submissions_daily_limit
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(f"Exception in {test_method.__name__}", False, f"Unexpected error: {str(e)}")
            print()  # Add spacing between tests
        
        # Print summary
        print("=" * 80)
        print(f"📊 REVIEW REQUEST TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ReviewRequestTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())