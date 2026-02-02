"""
Test suite for Submissions Management feature:
1. Submissions button with notification badge on admin dashboard
2. Navigation to /admin/submissions page
3. Status filters (ALL, PENDING, APPROVED, REJECTED)
4. Individual submission selection with checkboxes
5. Select All checkbox functionality
6. Bulk APPROVE button with count
7. Bulk DELETE button with count
8. Individual approve/reject/delete buttons
9. Back button navigation
10. Red notification badge for pending submissions
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSubmissionsAPI:
    """Test submissions API endpoints"""
    
    def test_get_submissions_pending(self):
        """Test getting pending submissions"""
        response = requests.get(f"{BASE_URL}/api/admin/submissions", params={"status": "pending", "limit": 50})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "pages" in data
        assert "page" in data
        print(f"✓ Pending submissions: {data['total']} total, {len(data['items'])} returned")
    
    def test_get_submissions_all(self):
        """Test getting all submissions (no status filter)"""
        response = requests.get(f"{BASE_URL}/api/admin/submissions", params={"limit": 50})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ All submissions (default pending): {data['total']} total")
    
    def test_get_submissions_approved(self):
        """Test getting approved submissions"""
        response = requests.get(f"{BASE_URL}/api/admin/submissions", params={"status": "approved", "limit": 50})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Approved submissions: {data['total']} total")
    
    def test_get_submissions_rejected(self):
        """Test getting rejected submissions"""
        response = requests.get(f"{BASE_URL}/api/admin/submissions", params={"status": "rejected", "limit": 50})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Rejected submissions: {data['total']} total")
    
    def test_get_unseen_count(self):
        """Test getting unseen/pending submissions count for notification badge"""
        response = requests.get(f"{BASE_URL}/api/admin/submissions/unseen-count")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)
        print(f"✓ Unseen/pending count: {data['count']}")


class TestSubmissionActions:
    """Test individual submission actions"""
    
    def test_approve_submission(self):
        """Test approving a submission"""
        # First get a pending submission
        response = requests.get(f"{BASE_URL}/api/admin/submissions", params={"status": "pending", "limit": 1})
        assert response.status_code == 200
        data = response.json()
        
        if data["items"]:
            submission_id = data["items"][0]["id"]
            
            # Approve it
            approve_response = requests.post(f"{BASE_URL}/api/admin/submissions/{submission_id}/approve")
            assert approve_response.status_code == 200
            approve_data = approve_response.json()
            assert approve_data.get("success") == True
            print(f"✓ Submission {submission_id} approved successfully")
        else:
            print("⚠ No pending submissions to test approve")
    
    def test_reject_submission(self):
        """Test rejecting a submission"""
        # First get a pending submission
        response = requests.get(f"{BASE_URL}/api/admin/submissions", params={"status": "pending", "limit": 1})
        assert response.status_code == 200
        data = response.json()
        
        if data["items"]:
            submission_id = data["items"][0]["id"]
            
            # Reject it
            reject_response = requests.post(f"{BASE_URL}/api/admin/submissions/{submission_id}/reject")
            assert reject_response.status_code == 200
            reject_data = reject_response.json()
            assert reject_data.get("success") == True
            print(f"✓ Submission {submission_id} rejected successfully")
        else:
            print("⚠ No pending submissions to test reject")
    
    def test_delete_submission(self):
        """Test deleting a submission"""
        # First get any submission (preferably rejected)
        response = requests.get(f"{BASE_URL}/api/admin/submissions", params={"status": "rejected", "limit": 1})
        assert response.status_code == 200
        data = response.json()
        
        if data["items"]:
            submission_id = data["items"][0]["id"]
            
            # Delete it
            delete_response = requests.delete(f"{BASE_URL}/api/admin/submissions/{submission_id}")
            assert delete_response.status_code == 200
            delete_data = delete_response.json()
            assert delete_data.get("success") == True
            print(f"✓ Submission {submission_id} deleted successfully")
        else:
            print("⚠ No rejected submissions to test delete")
    
    def test_approve_nonexistent_submission(self):
        """Test approving a non-existent submission returns 404"""
        response = requests.post(f"{BASE_URL}/api/admin/submissions/nonexistent-id-12345/approve")
        assert response.status_code == 404
        print("✓ Non-existent submission approve returns 404")
    
    def test_reject_nonexistent_submission(self):
        """Test rejecting a non-existent submission returns 404"""
        response = requests.post(f"{BASE_URL}/api/admin/submissions/nonexistent-id-12345/reject")
        assert response.status_code == 404
        print("✓ Non-existent submission reject returns 404")
    
    def test_delete_nonexistent_submission(self):
        """Test deleting a non-existent submission returns 404"""
        response = requests.delete(f"{BASE_URL}/api/admin/submissions/nonexistent-id-12345")
        assert response.status_code == 404
        print("✓ Non-existent submission delete returns 404")


class TestAdminLogin:
    """Test admin login for authenticated operations"""
    
    def test_admin_login_success(self):
        """Test admin login with correct password"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={"password": "admin123"})
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("✓ Admin login successful with password 'admin123'")
    
    def test_admin_login_failure(self):
        """Test admin login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={"password": "wrongpassword"})
        assert response.status_code == 401
        print("✓ Admin login fails with wrong password")


class TestSubmissionsPagination:
    """Test submissions pagination"""
    
    def test_pagination_page_1(self):
        """Test getting first page of submissions"""
        response = requests.get(f"{BASE_URL}/api/admin/submissions", params={"page": 1, "limit": 10, "status": "pending"})
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert len(data["items"]) <= 10
        print(f"✓ Page 1: {len(data['items'])} items, total pages: {data['pages']}")
    
    def test_pagination_page_2(self):
        """Test getting second page of submissions"""
        response = requests.get(f"{BASE_URL}/api/admin/submissions", params={"page": 2, "limit": 10, "status": "pending"})
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        print(f"✓ Page 2: {len(data['items'])} items")


class TestBulkOperationsPrep:
    """Test preparation for bulk operations (verify data structure)"""
    
    def test_submission_has_id(self):
        """Test that submissions have ID field for selection"""
        response = requests.get(f"{BASE_URL}/api/admin/submissions", params={"limit": 5})
        assert response.status_code == 200
        data = response.json()
        
        if data["items"]:
            for item in data["items"]:
                assert "id" in item
                assert "status" in item
                assert "name" in item
            print(f"✓ All {len(data['items'])} submissions have required fields (id, status, name)")
        else:
            print("⚠ No submissions to verify structure")
    
    def test_submission_status_values(self):
        """Test that submission status values are valid"""
        response = requests.get(f"{BASE_URL}/api/admin/submissions", params={"limit": 50})
        assert response.status_code == 200
        data = response.json()
        
        valid_statuses = {"pending", "approved", "rejected"}
        for item in data["items"]:
            assert item["status"] in valid_statuses, f"Invalid status: {item['status']}"
        
        print(f"✓ All submissions have valid status values")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
