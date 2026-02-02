#!/usr/bin/env python3
"""
Security-focused backend tests for the review request
"""
import requests
import sys
import json

class SecurityTester:
    def __init__(self, base_url="https://downloadportal-1.preview.emergentagent.com/api"):
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

            success = expected_status is None or response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected: {expected_status})"
                try:
                    error_data = response.json()
                    details += f" - {error_data}"
                except:
                    details += f" - {response.text[:100]}"

            self.log_test(name, success, details)
            
            # Return response data for further validation
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {}
                
            return success, response_data

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_1_settings_no_secret_keys(self):
        """1) Verify /api/settings does NOT expose resend_api_key or recaptcha_secret_key"""
        success, response = self.run_test("1. Settings No Secret Keys", "GET", "settings", 200)
        if success:
            resend_key = response.get('resend_api_key')
            recaptcha_secret = response.get('recaptcha_secret_key')
            
            if resend_key is None and recaptcha_secret is None:
                print(f"   ✓ Both resend_api_key and recaptcha_secret_key are properly hidden")
                return True
            else:
                exposed_keys = []
                if resend_key is not None:
                    exposed_keys.append(f"resend_api_key: {resend_key}")
                if recaptcha_secret is not None:
                    exposed_keys.append(f"recaptcha_secret_key: {recaptcha_secret}")
                print(f"   ✗ Secret keys exposed: {', '.join(exposed_keys)}")
                return False
        return success

    def test_2_admin_resend_hides_key(self):
        """2) Verify /api/admin/resend updates sender email and hides api key in response"""
        resend_update = {
            "resend_api_key": "re_test_key_12345",
            "resend_sender_email": "test@example.com"
        }
        
        success, response = self.run_test("2. Admin Resend Update", "PUT", "admin/resend", 200, resend_update)
        if success:
            api_key = response.get('resend_api_key')
            sender_email = response.get('resend_sender_email')
            
            if api_key is None and sender_email == "test@example.com":
                print(f"   ✓ API key hidden, sender email updated to: {sender_email}")
                return True
            else:
                print(f"   ✗ API key exposed: {api_key}, sender: {sender_email}")
                return False
        return success

    def test_3_forgot_password_no_leakage(self):
        """3) Verify /api/auth/forgot-password returns success for both existing and non-existing emails"""
        # Test with non-existing email
        non_existing_email = {"email": "nonexistent@example.com"}
        success1, response1 = self.run_test("3a. Forgot Password Non-Existing Email", "POST", "auth/forgot-password", 200, non_existing_email)
        
        # Test with existing email
        existing_email = {"email": "test@example.com"}
        success2, response2 = self.run_test("3b. Forgot Password Existing Email", "POST", "auth/forgot-password", 200, existing_email)
        
        if success1 and success2:
            if response1.get('success') == True and response2.get('success') == True:
                print(f"   ✓ Both existing and non-existing emails return success (no leakage)")
                return True
            else:
                print(f"   ✗ Different responses: {response1}, {response2}")
                return False
        return success1 and success2

    def test_4_reset_password_bad_token(self):
        """4) Verify /api/auth/reset-password with bad token returns 400"""
        bad_token_request = {
            "token": "invalid_token_12345",
            "new_password": "newpassword123"
        }
        
        success, response = self.run_test("4. Reset Password Bad Token", "POST", "auth/reset-password", 400, bad_token_request)
        if success:
            print(f"   ✓ Bad token properly rejected with 400")
        return success

    def test_5_admin_init_already_initialized(self):
        """5) Verify /api/admin/init returns 400 if already initialized"""
        init_request = {
            "email": "admin@example.com",
            "password": "newadminpass123"
        }
        
        success, response = self.run_test("5. Admin Init Already Initialized", "POST", "admin/init", 400, init_request)
        if success:
            print(f"   ✓ Admin init properly rejects re-initialization with 400")
        return success

    def test_6_admin_password_change_validation(self):
        """6) Verify /api/admin/password/change/request validation"""
        # Test without current password (should fail with 422)
        invalid_request = {"new_password": "newpass123"}
        fail_success, _ = self.run_test("6a. Password Change No Current Password", "POST", "admin/password/change/request", 422, invalid_request)
        
        # Test with wrong current password (should fail with 401)
        wrong_password_request = {
            "current_password": "wrongpassword",
            "new_password": "newpass123"
        }
        wrong_success, _ = self.run_test("6b. Password Change Wrong Current Password", "POST", "admin/password/change/request", 401, wrong_password_request)
        
        # Clear resend configuration
        clear_resend = {"resend_api_key": "", "resend_sender_email": ""}
        self.run_test("6c. Clear Resend Config", "PUT", "admin/resend", 200, clear_resend)
        
        # Test with correct password but no resend config (should return 500 or 520)
        correct_password_request = {
            "current_password": "newpass123",  # Current admin password
            "new_password": "newerpass123"
        }
        no_resend_success, no_resend_response = self.run_test("6d. Password Change No Resend Config", "POST", "admin/password/change/request", None, correct_password_request)
        
        # Check if it's 500 or 520 (both acceptable for email failure)
        if no_resend_response and no_resend_response.get('detail') == "Failed to send confirmation email":
            no_resend_success = True
            print(f"   ✓ Correct error message returned for email failure")
        else:
            no_resend_success = False
        
        if fail_success and wrong_success and no_resend_success:
            print(f"   ✓ All password change validations work correctly")
            return True
        else:
            print(f"   ✗ Some validations failed: missing field={fail_success}, wrong password={wrong_success}, no resend={no_resend_success}")
            return False

    def test_7_admin_password_change_confirm_bad_token(self):
        """7) Verify /api/admin/password/change/confirm with bad token returns 400"""
        bad_token_request = {"token": "invalid_admin_token_12345"}
        success, response = self.run_test("7. Admin Password Change Confirm Bad Token", "POST", "admin/password/change/confirm", 400, bad_token_request)
        if success:
            print(f"   ✓ Bad token properly rejected with 400")
        return success

    def test_8_admin_forgot_reset_bad_tokens(self):
        """8) Verify /api/admin/forgot-password and /api/admin/reset-password bad token behavior"""
        # Test admin forgot password
        forgot_request = {"email": "admin@example.com"}
        forgot_success, _ = self.run_test("8a. Admin Forgot Password", "POST", "admin/forgot-password", 200, forgot_request)
        
        # Test admin reset password with bad token
        bad_reset_request = {
            "token": "invalid_admin_reset_token",
            "new_password": "newadminpass123"
        }
        reset_success, _ = self.run_test("8b. Admin Reset Password Bad Token", "POST", "admin/reset-password", 400, bad_reset_request)
        
        if forgot_success and reset_success:
            print(f"   ✓ Admin forgot password works, bad reset token properly rejected")
            return True
        else:
            print(f"   ✗ Admin forgot/reset issues: forgot={forgot_success}, reset={reset_success}")
            return False

    def test_9_admin_login_db_priority(self):
        """9) Verify /api/admin/login uses DB-stored admin_password_hash"""
        # Test login with the DB-stored password
        db_password_login = {"password": "newpass123"}  # Current DB password
        db_success, _ = self.run_test("9a. Admin Login DB Password", "POST", "admin/login", 200, db_password_login)
        
        # Test login with potential env password (should fail)
        env_password_login = {"password": "admin123"}  # Potential env default
        env_success, _ = self.run_test("9b. Admin Login Env Password Should Fail", "POST", "admin/login", 401, env_password_login)
        
        if db_success and env_success:
            print(f"   ✓ DB password works, env password properly rejected")
            return True
        else:
            print(f"   ✗ Admin login priority issues: DB={db_success}, env rejection={env_success}")
            return False

def main():
    print("🔒 Security Tests for Review Request")
    print("=" * 60)
    
    tester = SecurityTester()
    
    # Run security tests in order
    test_methods = [
        tester.test_1_settings_no_secret_keys,
        tester.test_2_admin_resend_hides_key,
        tester.test_3_forgot_password_no_leakage,
        tester.test_4_reset_password_bad_token,
        tester.test_5_admin_init_already_initialized,
        tester.test_6_admin_password_change_validation,
        tester.test_7_admin_password_change_confirm_bad_token,
        tester.test_8_admin_forgot_reset_bad_tokens,
        tester.test_9_admin_login_db_priority,
    ]
    
    for test_method in test_methods:
        test_method()
        print()
    
    # Print summary
    print("=" * 60)
    print(f"📊 SECURITY TEST SUMMARY")
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