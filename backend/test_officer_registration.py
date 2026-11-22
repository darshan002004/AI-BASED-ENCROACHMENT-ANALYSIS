import sys
import uuid
import httpx

BASE_URL = "http://127.0.0.1:8000/api"

def test_all_officer_registration_scenarios():
    client = httpx.Client(timeout=15.0)
    print("=" * 70)
    print("ENCROWATCH AI — OFFICER & CITIZEN REGISTRATION VERIFICATION SUITE")
    print("=" * 70)

    # Setup unique identifiers for test run
    uid = uuid.uuid4().hex[:6]
    cit_email = f"citizen_test_{uid}@encrowatch.ai"
    cit_pass = "citPassword123!"

    off_email_1 = f"officer_app_{uid}@bbmp.gov.in"
    off_pass_1 = "officerPass123!"
    off_emp_id_1 = f"MUNI-EMP-{uid}-A"

    off_email_2 = f"officer_rej_{uid}@bbmp.gov.in"
    off_pass_2 = "officerPass123!"
    off_emp_id_2 = f"MUNI-EMP-{uid}-B"

    # Admin credentials for approvals
    admin_login_res = client.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@encrowatch.ai", "password": "admin123"}
    )
    assert admin_login_res.status_code == 200, f"Admin login failed: {admin_login_res.text}"
    admin_token = admin_login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[PASS] 0. Administrator authenticated for supervision actions")

    # ---------------------------------------------------------
    # Scenario 1: Citizen can register successfully
    # ---------------------------------------------------------
    cit_reg_res = client.post(
        f"{BASE_URL}/auth/register",
        json={
            "full_name": "Test Citizen Verma",
            "email": cit_email,
            "phone": "+91 98765 11111",
            "address": "Indiranagar 100ft Road, Bengaluru",
            "password": cit_pass
        }
    )
    assert cit_reg_res.status_code == 200, f"Citizen registration failed: {cit_reg_res.text}"
    cit_reg_data = cit_reg_res.json()
    assert cit_reg_data["user"]["role"] == "citizen"
    assert cit_reg_data["user"]["approval_status"] == "approved"
    assert "access_token" in cit_reg_data
    print(f"[PASS] 1. Citizen registered successfully (Role='citizen', Status='approved', Token issued)")

    # ---------------------------------------------------------
    # Scenario 2: Citizen can log in and access Citizen Dashboard
    # ---------------------------------------------------------
    cit_login_res = client.post(
        f"{BASE_URL}/auth/login",
        json={"email": cit_email, "password": cit_pass}
    )
    assert cit_login_res.status_code == 200, f"Citizen login failed: {cit_login_res.text}"
    cit_token = cit_login_res.json()["access_token"]
    cit_headers = {"Authorization": f"Bearer {cit_token}"}

    # Verify citizen can access citizen endpoints
    cit_inc_res = client.get(f"{BASE_URL}/incidents?my_reports=true", headers=cit_headers)
    assert cit_inc_res.status_code == 200
    print("[PASS] 2. Citizen can log in and access citizen reporting portal")

    # ---------------------------------------------------------
    # Scenario 3: Officer can submit a registration request
    # ---------------------------------------------------------
    off_reg_res = client.post(
        f"{BASE_URL}/auth/register-officer",
        json={
            "full_name": "Applicant Inspector R. Kumar",
            "email": off_email_1,
            "phone": "+91 98765 22222",
            "employee_id": off_emp_id_1,
            "department": "Encroachment Removal Squad",
            "designation": "Ward Enforcement Officer",
            "assigned_area": "East Zone - Ward 84",
            "password": off_pass_1
        }
    )
    assert off_reg_res.status_code == 200, f"Officer registration request failed: {off_reg_res.text}"
    off_app_data = off_reg_res.json()
    off_id_1 = off_app_data["id"]
    assert off_app_data["approval_status"] == "pending_approval"
    assert "access_token" not in off_app_data, "Pending officer must NOT receive an access token!"
    print(f"[PASS] 3. Officer submitted registration request (ID: {off_id_1}, Status='pending_approval', No Token)")

    # ---------------------------------------------------------
    # Scenario 4: Pending officer cannot access Officer Dashboard (Login blocked)
    # ---------------------------------------------------------
    off_pending_login = client.post(
        f"{BASE_URL}/auth/login",
        json={"email": off_email_1, "password": off_pass_1}
    )
    assert off_pending_login.status_code == 403, f"Expected 403 for pending officer, got: {off_pending_login.status_code}"
    assert "awaiting administrator approval" in off_pending_login.json()["detail"].lower()
    print("[PASS] 4. Pending officer login rejected with HTTP 403 ('awaiting administrator approval')")

    # ---------------------------------------------------------
    # Scenario 5: Admin can see pending officer applications
    # ---------------------------------------------------------
    pending_list_res = client.get(f"{BASE_URL}/auth/officers/pending", headers=admin_headers)
    assert pending_list_res.status_code == 200, f"Listing pending officers failed: {pending_list_res.text}"
    pending_items = pending_list_res.json()
    found_pending = any(o["id"] == off_id_1 for o in pending_items)
    assert found_pending, f"Officer {off_id_1} not found in pending list: {pending_items}"
    print(f"[PASS] 5. Admin can inspect pending officer applications (Found {len(pending_items)} in queue)")

    # ---------------------------------------------------------
    # Scenario 6: Admin can approve an officer
    # ---------------------------------------------------------
    approve_res = client.post(f"{BASE_URL}/auth/officers/{off_id_1}/approve", headers=admin_headers)
    assert approve_res.status_code == 200, f"Officer approval failed: {approve_res.text}"
    approved_data = approve_res.json()
    assert approved_data["approval_status"] == "approved"
    assert approved_data["is_active"] is True
    assert approved_data["role"] == "officer"
    print(f"[PASS] 6. Admin approved officer {off_id_1} (Status='approved', is_active=True, Role='officer')")

    # ---------------------------------------------------------
    # Scenario 7: Approved officer can log in successfully
    # ---------------------------------------------------------
    approved_login_res = client.post(
        f"{BASE_URL}/auth/login",
        json={"email": off_email_1, "password": off_pass_1}
    )
    assert approved_login_res.status_code == 200, f"Approved officer login failed: {approved_login_res.text}"
    approved_token = approved_login_res.json()["access_token"]
    approved_headers = {"Authorization": f"Bearer {approved_token}"}
    print("[PASS] 7. Approved officer logged in successfully and received active JWT token")

    # ---------------------------------------------------------
    # Scenario 8: Approved officer accesses Officer Dashboard / protected review queue
    # ---------------------------------------------------------
    review_q_res = client.get(f"{BASE_URL}/incidents/review-queue", headers=approved_headers)
    assert review_q_res.status_code == 200, f"Officer review queue access failed: {review_q_res.text}"
    print("[PASS] 8. Approved officer accessed Officer Dashboard protected review queue")

    # ---------------------------------------------------------
    # Scenario 9: Admin can reject an officer application
    # ---------------------------------------------------------
    # Register second officer
    reg2_res = client.post(
        f"{BASE_URL}/auth/register-officer",
        json={
            "full_name": "Declined Applicant Rao",
            "email": off_email_2,
            "phone": "+91 98765 33333",
            "employee_id": off_emp_id_2,
            "department": "Traffic Management & Mobility",
            "designation": "Junior Engineer",
            "assigned_area": "West Zone",
            "password": off_pass_2
        }
    )
    assert reg2_res.status_code == 200
    off_id_2 = reg2_res.json()["id"]

    # Reject with specific reason
    reject_reason = "Employee ID does not match the active municipal roster."
    reject_res = client.post(
        f"{BASE_URL}/auth/officers/{off_id_2}/reject",
        headers=admin_headers,
        json={"reason": reject_reason}
    )
    assert reject_res.status_code == 200, f"Reject failed: {reject_res.text}"
    rejected_data = reject_res.json()
    assert rejected_data["approval_status"] == "rejected"
    assert rejected_data["is_active"] is False
    assert rejected_data["rejection_reason"] == reject_reason
    print(f"[PASS] 9. Admin rejected officer application {off_id_2} with documented reason")

    # ---------------------------------------------------------
    # Scenario 10: Rejected officer cannot access officer functionality
    # ---------------------------------------------------------
    rejected_login = client.post(
        f"{BASE_URL}/auth/login",
        json={"email": off_email_2, "password": off_pass_2}
    )
    assert rejected_login.status_code == 403, f"Expected 403, got: {rejected_login.status_code}"
    assert "rejected" in rejected_login.json()["detail"].lower()
    print("[PASS] 10. Rejected officer login blocked with HTTP 403 and rejection reason details")

    # ---------------------------------------------------------
    # Scenario 11: Duplicate email registration is rejected
    # ---------------------------------------------------------
    dup_email_res = client.post(
        f"{BASE_URL}/auth/register-officer",
        json={
            "full_name": "Duplicate Email Attempt",
            "email": cit_email,  # already used by citizen
            "phone": "+91 98765 44444",
            "employee_id": f"MUNI-DIFF-{uid}",
            "department": "Public Works",
            "designation": "Inspector",
            "assigned_area": "Central Core",
            "password": "password123"
        }
    )
    assert dup_email_res.status_code == 400, f"Expected 400, got: {dup_email_res.status_code}"
    print("[PASS] 11. Duplicate email registration rejected with HTTP 400")

    # ---------------------------------------------------------
    # Scenario 12: Duplicate employee ID registration is rejected
    # ---------------------------------------------------------
    dup_emp_res = client.post(
        f"{BASE_URL}/auth/register-officer",
        json={
            "full_name": "Duplicate Employee ID Attempt",
            "email": f"diff_email_{uid}@bbmp.gov.in",
            "phone": "+91 98765 55555",
            "employee_id": off_emp_id_1,  # already used by officer 1
            "department": "Public Works",
            "designation": "Inspector",
            "assigned_area": "Central Core",
            "password": "password123"
        }
    )
    assert dup_emp_res.status_code == 400, f"Expected 400, got: {dup_emp_res.status_code}"
    assert "employee id" in dup_emp_res.json()["detail"].lower()
    print("[PASS] 12. Duplicate Employee ID registration rejected with HTTP 400")

    # ---------------------------------------------------------
    # Scenario 13: Public Admin registration is blocked
    # ---------------------------------------------------------
    sneaky_admin_res = client.post(
        f"{BASE_URL}/auth/register",
        json={
            "full_name": "Privilege Escalation Attempt",
            "email": f"sneaky_admin_{uid}@gmail.com",
            "phone": "+91 98765 66666",
            "role": "admin",  # Attacker tries to pass admin role in public registration
            "password": "password123"
        }
    )
    assert sneaky_admin_res.status_code == 200
    sneaky_data = sneaky_admin_res.json()
    assert sneaky_data["user"]["role"] == "citizen", f"Public registration must force citizen! Got: {sneaky_data['user']['role']}"
    print("[PASS] 13. Public Admin registration blocked (Untrusted client role overwritten with 'citizen')")

    # ---------------------------------------------------------
    # Scenario 14: Unauthorized users cannot approve or reject applications
    # ---------------------------------------------------------
    # Citizen trying to approve
    cit_approve_attempt = client.post(
        f"{BASE_URL}/auth/officers/{off_id_2}/approve",
        headers=cit_headers
    )
    assert cit_approve_attempt.status_code == 403, f"Expected 403, got: {cit_approve_attempt.status_code}"

    # Unauthenticated attempt to approve
    anon_approve_attempt = client.post(f"{BASE_URL}/auth/officers/{off_id_2}/approve")
    assert anon_approve_attempt.status_code == 401, f"Expected 401, got: {anon_approve_attempt.status_code}"
    print("[PASS] 14. Unauthorized users prevented from approving/rejecting applications (403/401 enforced)")

    # ---------------------------------------------------------
    # Scenario 15: Existing login and incident-management features still work
    # ---------------------------------------------------------
    for role_name, email, pwd, expected_role in [
        ("Administrator", "admin@encrowatch.ai", "admin123", "admin"),
        ("Field Officer", "officer@encrowatch.ai", "officer123", "officer"),
        ("Citizen", "citizen@encrowatch.ai", "citizen123", "citizen")
    ]:
        login_res = client.post(f"{BASE_URL}/auth/login", json={"email": email, "password": pwd})
        assert login_res.status_code == 200, f"Login failed for {email}: {login_res.text}"
        data = login_res.json()
        assert data["user"]["role"] == expected_role
        tok = data["access_token"]
        # Verify authenticated endpoint access
        me_res = client.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {tok}"})
        assert me_res.status_code == 200
    print("[PASS] 15. Existing accounts (admin, officer, citizen) login and operational features preserved intact")

    print("=" * 70)
    print("ALL 15 TEST SCENARIOS PASSED SUCCESSFULLY (15/15)")
    print("=" * 70)

if __name__ == "__main__":
    test_all_officer_registration_scenarios()
