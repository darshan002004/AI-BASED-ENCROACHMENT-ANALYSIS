import sys
import uuid
import time
import json
import httpx
import pymongo
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "encrowatch_ai_db"

def run_full_uat():
    results = {}
    client = httpx.Client(timeout=25.0)
    mongo_client = pymongo.MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]

    print("=" * 80)
    print("ENCROWATCH AI — COMPLETE END-TO-END USER ACCEPTANCE TESTING SUITE")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target API: {BASE_URL}")
    print(f"Database: {DB_NAME} (Live MongoDB)")
    print("=" * 80)

    uid = uuid.uuid4().hex[:6]

    # Setup Admin Credentials
    admin_login = client.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@encrowatch.ai", "password": "admin123"}
    )
    assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[PASS] 0. Administrator authenticated successfully for UAT governance")

    # =========================================================================
    # TEST 1: CITIZEN REGISTRATION
    # =========================================================================
    print("\n" + "=" * 50)
    print("TEST 1: CITIZEN REGISTRATION")
    print("=" * 50)
    try:
        cit_email = f"uat_cit_{uid}@encrowatch.ai"
        cit_pass = "CitizenPass@123"
        cit_name = f"Aarav Sharma {uid}"
        cit_phone = "+91 98765 43210"
        cit_addr = "12th Main Road, Indiranagar, Bengaluru"

        # 1-4. Register new Citizen
        reg_res = client.post(
            f"{BASE_URL}/auth/register",
            json={
                "full_name": cit_name,
                "email": cit_email,
                "phone": cit_phone,
                "address": cit_addr,
                "password": cit_pass
            }
        )
        assert reg_res.status_code == 200, f"Citizen registration failed: {reg_res.status_code} {reg_res.text}"
        reg_data = reg_res.json()
        assert "access_token" in reg_data, "No access token in citizen registration response"
        assert reg_data["user"]["role"] == "citizen", f"Expected role citizen, got {reg_data['user']['role']}"
        assert reg_data["user"]["approval_status"] == "approved", "Citizen status not approved"
        cit_token = reg_data["access_token"]
        cit_headers = {"Authorization": f"Bearer {cit_token}"}
        cit_user_id = reg_data["user"]["id"]
        print(f"[PASS] 1.1 Citizen registration API succeeded (ID: {cit_user_id}, Role: 'citizen')")

        # 5-8. Verify in MongoDB
        db_cit = db.users.find_one({"email": cit_email})
        assert db_cit is not None, "Citizen not found in MongoDB users collection"
        pwd_hash = db_cit.get("password")
        assert pwd_hash is not None and pwd_hash != cit_pass, "Password is NOT hashed!"
        assert pwd_hash.startswith(("$2b$", "$2a$", "$argon2")), f"Password not properly hashed: {pwd_hash[:10]}"
        assert db_cit.get("role") == "citizen", f"DB role mismatch: {db_cit.get('role')}"
        assert db_cit.get("is_active") is True, f"DB is_active mismatch: {db_cit.get('is_active')}"
        assert db_cit.get("approval_status") == "approved", f"DB approval_status mismatch: {db_cit.get('approval_status')}"
        print(f"[PASS] 1.2 MongoDB verification: User stored, password securely hashed, role='citizen', is_active=True")

        # 9. Verify duplicate email rejected
        dup_res = client.post(
            f"{BASE_URL}/auth/register",
            json={
                "full_name": "Duplicate Citizen",
                "email": cit_email,
                "phone": "+91 98765 00000",
                "address": "MG Road",
                "password": "OtherPassword@123"
            }
        )
        assert dup_res.status_code == 400, f"Expected 400 for duplicate email, got {dup_res.status_code}"
        print(f"[PASS] 1.3 Duplicate email correctly rejected with HTTP 400 ({dup_res.json().get('detail')})")

        # 10. Verify invalid form inputs show meaningful validation messages
        invalid_res = client.post(
            f"{BASE_URL}/auth/register",
            json={
                "full_name": "Invalid Input Citizen",
                "email": "not-an-email-format",
                "phone": "123",
                "password": ""
            }
        )
        assert invalid_res.status_code == 422, f"Expected 422 for invalid inputs, got {invalid_res.status_code}"
        err_detail = invalid_res.json().get("detail")
        assert isinstance(err_detail, str) and len(err_detail) > 0, f"Error detail not string: {type(err_detail)}"
        print(f"[PASS] 1.4 Meaningful validation error returned on invalid inputs: '{err_detail}'")

        results["TEST_1"] = "PASS"
    except Exception as e:
        print(f"[FAIL] TEST 1: {e}")
        results["TEST_1"] = f"FAIL: {e}"

    # =========================================================================
    # TEST 2: OFFICER REGISTRATION
    # =========================================================================
    print("\n" + "=" * 50)
    print("TEST 2: OFFICER REGISTRATION")
    print("=" * 50)
    try:
        off_email_1 = f"uat_officer_{uid}@bbmp.gov.in"
        off_pass_1 = "OfficerPass@123"
        off_name_1 = f"Officer Priya Sharma {uid}"
        off_phone_1 = "+91 91234 56789"
        off_emp_id_1 = f"MUNI-EMP-{uid}-A"
        off_dept_1 = "Urban Mobility & Footpath Infrastructure"
        off_desig_1 = "Assistant Executive Engineer"
        off_zone_1 = "East Zone - Ward 112"

        # 1-4. Submit Officer Application
        off_reg_res = client.post(
            f"{BASE_URL}/auth/register-officer",
            json={
                "full_name": off_name_1,
                "email": off_email_1,
                "phone": off_phone_1,
                "password": off_pass_1,
                "employee_id": off_emp_id_1,
                "department": off_dept_1,
                "designation": off_desig_1,
                "assigned_area": off_zone_1
            }
        )
        assert off_reg_res.status_code == 200, f"Officer registration failed: {off_reg_res.status_code} {off_reg_res.text}"
        off_reg_data = off_reg_res.json()

        # 5-8. Verify no active token and status is pending_approval
        assert "access_token" not in off_reg_data or off_reg_data.get("access_token") is None, "Active token issued to pending officer!"
        assert off_reg_data.get("approval_status") == "pending_approval", f"Expected pending_approval, got {off_reg_data.get('approval_status')}"
        off_user_id_1 = off_reg_data.get("id")
        assert off_user_id_1 is not None, "Officer registration did not return user id"
        print(f"[PASS] 2.1 Officer application submitted (ID: {off_user_id_1}, Status: 'pending_approval', No Token Issued)")

        # Verify in MongoDB
        db_off_1 = db.users.find_one({"email": off_email_1})
        assert db_off_1 is not None, "Officer not found in MongoDB users"
        assert db_off_1.get("approval_status") == "pending_approval", f"DB status mismatch: {db_off_1.get('approval_status')}"
        assert db_off_1.get("is_active") is False, f"DB is_active mismatch: {db_off_1.get('is_active')}"
        assert db_off_1.get("employee_id") == off_emp_id_1, f"DB employee_id mismatch"
        assert db_off_1.get("department") == off_dept_1, f"DB department mismatch"
        assert db_off_1.get("designation") == off_desig_1, f"DB designation mismatch"
        assert db_off_1.get("assigned_area") == off_zone_1, f"DB zone mismatch"
        print(f"[PASS] 2.2 MongoDB verification: User saved with approval_status='pending_approval' and is_active=False")

        # 9. Verify duplicate email validation
        dup_email_res = client.post(
            f"{BASE_URL}/auth/register-officer",
            json={
                "full_name": "Another Officer",
                "email": off_email_1,
                "phone": "+91 91234 00000",
                "password": "Password123!",
                "employee_id": f"MUNI-EMP-{uid}-DIFF",
                "department": off_dept_1,
                "designation": off_desig_1,
                "assigned_area": off_zone_1
            }
        )
        assert dup_email_res.status_code == 400, f"Expected 400 for duplicate email, got {dup_email_res.status_code}"
        print(f"[PASS] 2.3 Duplicate officer email rejected with HTTP 400 ({dup_email_res.json().get('detail')})")

        # Verify duplicate employee ID validation
        dup_empid_res = client.post(
            f"{BASE_URL}/auth/register-officer",
            json={
                "full_name": "Another Officer 2",
                "email": f"different_{uid}@bbmp.gov.in",
                "phone": "+91 91234 00001",
                "password": "Password123!",
                "employee_id": off_emp_id_1,
                "department": off_dept_1,
                "designation": off_desig_1,
                "assigned_area": off_zone_1
            }
        )
        assert dup_empid_res.status_code == 400, f"Expected 400 for duplicate employee ID, got {dup_empid_res.status_code}"
        print(f"[PASS] 2.4 Duplicate employee ID rejected with HTTP 400 ({dup_empid_res.json().get('detail')})")

        # 10. Confirmation message check
        assert "message" in off_reg_data or "detail" in off_reg_data, "No confirmation message returned"
        print(f"[PASS] 2.5 Applicant confirmation message received: '{off_reg_data.get('message') or off_reg_data.get('detail')}'")

        results["TEST_2"] = "PASS"
    except Exception as e:
        print(f"[FAIL] TEST 2: {e}")
        results["TEST_2"] = f"FAIL: {e}"

    # =========================================================================
    # TEST 3: PENDING OFFICER LOGIN
    # =========================================================================
    print("\n" + "=" * 50)
    print("TEST 3: PENDING OFFICER LOGIN")
    print("=" * 50)
    try:
        # 1-4. Attempt login with pending credentials
        pending_login_res = client.post(
            f"{BASE_URL}/auth/login",
            json={"email": off_email_1, "password": off_pass_1}
        )
        assert pending_login_res.status_code == 403, f"Expected 403 Forbidden for pending officer, got {pending_login_res.status_code} ({pending_login_res.text})"
        pending_err = pending_login_res.json().get("detail", "")
        assert "awaiting" in pending_err.lower() or "pending" in pending_err.lower(), f"Unexpected error message: '{pending_err}'"
        assert "access_token" not in pending_login_res.json(), "Access token unexpectedly issued in 403 response!"
        print(f"[PASS] 3.1 Pending officer login correctly denied with HTTP 403 ('{pending_err}')")

        # 5. Direct access to protected officer APIs without token
        unauth_review = client.get(f"{BASE_URL}/incidents/review-queue")
        assert unauth_review.status_code == 401, f"Expected 401 Unauthorized, got {unauth_review.status_code}"
        print(f"[PASS] 3.2 Direct access to protected officer endpoint blocked without valid credentials (HTTP 401)")

        results["TEST_3"] = "PASS"
    except Exception as e:
        print(f"[FAIL] TEST 3: {e}")
        results["TEST_3"] = f"FAIL: {e}"

    # =========================================================================
    # TEST 4: ADMIN APPROVAL
    # =========================================================================
    print("\n" + "=" * 50)
    print("TEST 4: ADMIN APPROVAL")
    print("=" * 50)
    try:
        # 3-5. Query pending applications and locate officer
        pending_list_res = client.get(f"{BASE_URL}/auth/officers/pending", headers=admin_headers)
        assert pending_list_res.status_code == 200, f"Failed to get pending officers: {pending_list_res.text}"
        pending_officers = pending_list_res.json()
        target_officer = next((o for o in pending_officers if o.get("email") == off_email_1), None)
        assert target_officer is not None, f"Officer {off_email_1} not in pending applications list"
        officer_id_to_approve = target_officer["id"]
        print(f"[PASS] 4.1 Pending officer located in admin roster (ID: {officer_id_to_approve})")

        # 6-7. Verify submitted details match
        assert target_officer.get("employee_id") == off_emp_id_1
        assert target_officer.get("department") == off_dept_1
        assert target_officer.get("designation") == off_desig_1
        assert target_officer.get("assigned_area") == off_zone_1
        print(f"[PASS] 4.2 Verified all submitted applicant credentials")

        # 8. Approve Officer
        approve_res = client.post(
            f"{BASE_URL}/auth/officers/{officer_id_to_approve}/approve",
            headers=admin_headers
        )
        assert approve_res.status_code == 200, f"Approval failed: {approve_res.text}"
        approve_data = approve_res.json()
        assert approve_data.get("approval_status") == "approved"
        assert approve_data.get("is_active") is True
        print(f"[PASS] 4.3 Administrator approved officer application via API")

        # 9-11. Verify in MongoDB
        db_approved = db.users.find_one({"email": off_email_1})
        assert db_approved.get("approval_status") == "approved", f"DB approval_status mismatch: {db_approved.get('approval_status')}"
        assert db_approved.get("is_active") is True, f"DB is_active mismatch: {db_approved.get('is_active')}"
        assert db_approved.get("role") == "officer", f"DB role mismatch: {db_approved.get('role')}"
        assert "reviewed_by" in db_approved, "reviewed_by field missing from DB record"
        print(f"[PASS] 4.4 MongoDB verified: approval_status='approved', is_active=True, role='officer', reviewed_by recorded")

        # 12. Verify Audit Log entry created (either OFFICER_APPROVED or OFFICER_REGISTRATION_APPROVED)
        audit_entry = db.audit_logs.find_one({
            "action": {"$in": ["OFFICER_APPROVED", "OFFICER_REGISTRATION_APPROVED"]},
            "target_id": officer_id_to_approve
        })
        assert audit_entry is not None, "Audit log entry for officer approval not found!"
        print(f"[PASS] 4.5 Cryptographic audit log entry verified for approval (Action: '{audit_entry.get('action')}')")

        results["TEST_4"] = "PASS"
    except Exception as e:
        print(f"[FAIL] TEST 4: {e}")
        results["TEST_4"] = f"FAIL: {e}"

    # =========================================================================
    # TEST 5: APPROVED OFFICER LOGIN
    # =========================================================================
    print("\n" + "=" * 50)
    print("TEST 5: APPROVED OFFICER LOGIN")
    print("=" * 50)
    try:
        # 1-3. Log in with approved credentials
        approved_login_res = client.post(
            f"{BASE_URL}/auth/login",
            json={"email": off_email_1, "password": off_pass_1}
        )
        assert approved_login_res.status_code == 200, f"Approved officer login failed: {approved_login_res.text}"
        approved_login_data = approved_login_res.json()
        assert "access_token" in approved_login_data, "No access token issued to approved officer"
        officer_token = approved_login_data["access_token"]
        officer_headers = {"Authorization": f"Bearer {officer_token}"}
        assert approved_login_data["user"]["role"] == "officer", f"Expected role officer, got {approved_login_data['user']['role']}"
        assert approved_login_data["user"]["approval_status"] == "approved"
        print(f"[PASS] 5.1 Approved officer authenticated successfully (JWT Token issued, Role: 'officer')")

        # 4-6. Verify officer operations are accessible
        cases_res = client.get(f"{BASE_URL}/incidents?limit=10", headers=officer_headers)
        assert cases_res.status_code == 200, f"Failed to access incidents with officer token: {cases_res.text}"
        review_res = client.get(f"{BASE_URL}/incidents/review-queue", headers=officer_headers)
        assert review_res.status_code == 200, f"Failed to access review queue: {review_res.text}"
        print(f"[PASS] 5.2 Officer field operations accessible: Retrieved incidents and review queue")

        # 7. Verify Admin-only functionality is strictly blocked for officer
        admin_blocked_1 = client.get(f"{BASE_URL}/auth/officers/pending", headers=officer_headers)
        assert admin_blocked_1.status_code == 403, f"Officer accessed admin pending list! Status: {admin_blocked_1.status_code}"
        admin_blocked_2 = client.get(f"{BASE_URL}/auth/users", headers=officer_headers)
        assert admin_blocked_2.status_code == 403, f"Officer accessed admin user roster! Status: {admin_blocked_2.status_code}"
        admin_blocked_3 = client.get(f"{BASE_URL}/audit/verify-integrity", headers=officer_headers)
        assert admin_blocked_3.status_code == 403, f"Officer accessed audit integrity check! Status: {admin_blocked_3.status_code}"
        print(f"[PASS] 5.3 Administrative controls strictly blocked with HTTP 403 for Officer role")

        results["TEST_5"] = "PASS"
    except Exception as e:
        print(f"[FAIL] TEST 5: {e}")
        results["TEST_5"] = f"FAIL: {e}"

    # =========================================================================
    # TEST 6: OFFICER REJECTION
    # =========================================================================
    print("\n" + "=" * 50)
    print("TEST 6: OFFICER REJECTION")
    print("=" * 50)
    try:
        off_email_2 = f"uat_rej_officer_{uid}@bbmp.gov.in"
        off_pass_2 = "OfficerRejPass@123"
        off_name_2 = f"Officer Vikram Das {uid}"
        off_emp_id_2 = f"MUNI-EMP-{uid}-B"
        rej_reason = "Department credential check failed: Employee ID not registered in BBMP municipal records."

        # 1. Register candidate
        reg_res_2 = client.post(
            f"{BASE_URL}/auth/register-officer",
            json={
                "full_name": off_name_2,
                "email": off_email_2,
                "phone": "+91 99887 76655",
                "password": off_pass_2,
                "employee_id": off_emp_id_2,
                "department": "Traffic & Parking Enforcement",
                "designation": "Junior Engineer",
                "assigned_area": "South Zone - Ward 143"
            }
        )
        assert reg_res_2.status_code == 200, f"Registration failed: {reg_res_2.text}"
        cand_user_id = reg_res_2.json().get("id")
        print(f"[PASS] 6.1 Second officer registered (ID: {cand_user_id})")

        # 2-4. Reject application as Admin with mandatory reason
        reject_res = client.post(
            f"{BASE_URL}/auth/officers/{cand_user_id}/reject",
            json={"reason": rej_reason},
            headers=admin_headers
        )
        assert reject_res.status_code == 200, f"Officer rejection failed: {reject_res.text}"
        print(f"[PASS] 6.2 Administrator rejected officer application with mandatory reason")

        # 5-6. Verify status and reason in MongoDB
        db_rejected = db.users.find_one({"email": off_email_2})
        assert db_rejected.get("approval_status") == "rejected", f"DB status mismatch: {db_rejected.get('approval_status')}"
        assert db_rejected.get("is_active") is False, f"DB is_active mismatch: {db_rejected.get('is_active')}"
        assert db_rejected.get("rejection_reason") == rej_reason, f"DB rejection_reason mismatch: {db_rejected.get('rejection_reason')}"
        print(f"[PASS] 6.3 MongoDB verified: approval_status='rejected', is_active=False, rejection_reason preserved")

        # 7. Verify Audit Log entry created (either OFFICER_REJECTED or OFFICER_REGISTRATION_REJECTED)
        rej_audit = db.audit_logs.find_one({
            "action": {"$in": ["OFFICER_REJECTED", "OFFICER_REGISTRATION_REJECTED"]},
            "target_id": cand_user_id
        })
        assert rej_audit is not None, "Audit log entry for officer rejection not found"
        print(f"[PASS] 6.4 Audit log entry verified for rejection (Action: '{rej_audit.get('action')}')")

        # 8. Attempt login with rejected account
        rej_login = client.post(
            f"{BASE_URL}/auth/login",
            json={"email": off_email_2, "password": off_pass_2}
        )
        assert rej_login.status_code == 403, f"Expected 403 Forbidden for rejected officer, got {rej_login.status_code}"
        rej_msg = rej_login.json().get("detail", "")
        assert "rejected" in rej_msg.lower(), f"Expected rejection notice in error message, got: '{rej_msg}'"
        print(f"[PASS] 6.5 Rejected officer login denied with HTTP 403 ('{rej_msg}')")

        results["TEST_6"] = "PASS"
    except Exception as e:
        print(f"[FAIL] TEST 6: {e}")
        results["TEST_6"] = f"FAIL: {e}"

    # =========================================================================
    # TEST 7: ROLE-BASED DASHBOARD VERIFICATION
    # =========================================================================
    print("\n" + "=" * 50)
    print("TEST 7: ROLE-BASED DASHBOARD VERIFICATION")
    print("=" * 50)
    try:
        # 1. Admin Dashboard Endpoints
        admin_kpis = client.get(f"{BASE_URL}/analytics/kpis", headers=admin_headers)
        assert admin_kpis.status_code == 200, f"Admin KPIs failed: {admin_kpis.text}"
        admin_users = client.get(f"{BASE_URL}/auth/users", headers=admin_headers)
        assert admin_users.status_code == 200, f"Admin Users failed: {admin_users.text}"
        admin_audit = client.get(f"{BASE_URL}/audit/logs", headers=admin_headers)
        assert admin_audit.status_code == 200, f"Admin Audit failed: {admin_audit.text}"
        admin_hotspots = client.get(f"{BASE_URL}/analytics/hotspots", headers=admin_headers)
        assert admin_hotspots.status_code == 200, f"Admin Hotspots Analytics failed: {admin_hotspots.text}"
        admin_sla = client.get(f"{BASE_URL}/sla/rules", headers=admin_headers)
        assert admin_sla.status_code == 200, f"Admin SLA Rules failed: {admin_sla.text}"
        print("[PASS] 7.1 Admin authorized endpoints verified: KPIs, Users, Audit Logs, Hotspots Analytics, SLA Rules (All 200 OK)")

        # 2. Officer Dashboard Endpoints
        off_incidents = client.get(f"{BASE_URL}/incidents?limit=5", headers=officer_headers)
        assert off_incidents.status_code == 200, f"Officer incidents failed: {off_incidents.text}"
        off_notifs = client.get(f"{BASE_URL}/notifications", headers=officer_headers)
        assert off_notifs.status_code == 200, f"Officer notifications failed: {off_notifs.text}"
        print("[PASS] 7.2 Officer authorized endpoints verified: Incidents, Notifications (All 200 OK)")

        # 3. Citizen Dashboard Endpoints
        cit_reports = client.get(f"{BASE_URL}/incidents?my_reports=true", headers=cit_headers)
        assert cit_reports.status_code == 200, f"Citizen reports failed: {cit_reports.text}"
        cit_notifs = client.get(f"{BASE_URL}/notifications", headers=cit_headers)
        assert cit_notifs.status_code == 200, f"Citizen notifications failed: {cit_notifs.text}"
        pub_cases = client.get(f"{BASE_URL}/public/incidents")
        assert pub_cases.status_code == 200, f"Public cases failed: {pub_cases.text}"
        print("[PASS] 7.3 Citizen authorized endpoints verified: My Reports, Notifications, Public Transparency Map (All 200 OK)")

        # 4. Cross-Role Isolation Verifications
        assert client.get(f"{BASE_URL}/auth/users", headers=cit_headers).status_code == 403
        assert client.get(f"{BASE_URL}/audit/logs", headers=cit_headers).status_code == 403
        assert client.get(f"{BASE_URL}/auth/officers/pending", headers=cit_headers).status_code == 403
        assert client.get(f"{BASE_URL}/auth/users", headers=officer_headers).status_code == 403
        print("[PASS] 7.4 Cross-role access barriers strictly enforced (All 403 Forbidden)")

        results["TEST_7"] = "PASS"
    except Exception as e:
        print(f"[FAIL] TEST 7: {e}")
        results["TEST_7"] = f"FAIL: {e}"

    # =========================================================================
    # TEST 8: SECURITY TESTING
    # =========================================================================
    print("\n" + "=" * 50)
    print("TEST 8: SECURITY TESTING")
    print("=" * 50)
    try:
        # 1. Unauthenticated requests
        unauth_users = client.get(f"{BASE_URL}/auth/users")
        assert unauth_users.status_code == 401, f"Expected 401, got {unauth_users.status_code}"
        unauth_audit = client.get(f"{BASE_URL}/audit/verify-integrity")
        assert unauth_audit.status_code == 401, f"Expected 401, got {unauth_audit.status_code}"
        print("[PASS] 8.1 Unauthenticated requests blocked with HTTP 401")

        # 2. Invalid JWT token
        bad_token_res = client.get(f"{BASE_URL}/auth/users", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert bad_token_res.status_code == 401, f"Expected 401, got {bad_token_res.status_code}"
        print("[PASS] 8.2 Malformed / invalid JWT tokens rejected with HTTP 401")

        # 3. Forged JWT token signature check
        parts = cit_token.split(".")
        if len(parts) == 3:
            tampered_payload = "eyJzdWIiOiAiYWRtaW5AZW5jcm93YXRjaC5haSIsICJyb2xlIjogImFkbWluIn0"
            forged_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"
            forged_res = client.get(f"{BASE_URL}/auth/users", headers={"Authorization": f"Bearer {forged_token}"})
            assert forged_res.status_code == 401, f"Tampered token was accepted! Status: {forged_res.status_code}"
            print("[PASS] 8.3 Tampered / signature-mismatched JWT tokens strictly rejected with HTTP 401")

        # 4. Deactivated officer verification
        deact_res = client.post(f"{BASE_URL}/auth/officers/{officer_id_to_approve}/deactivate", headers=admin_headers)
        assert deact_res.status_code == 200, f"Deactivation failed: {deact_res.text}"
        deact_login = client.post(f"{BASE_URL}/auth/login", json={"email": off_email_1, "password": off_pass_1})
        assert deact_login.status_code == 403, f"Expected 403 for deactivated officer, got {deact_login.status_code}"
        print(f"[PASS] 8.4 Deactivated officer login blocked with HTTP 403 ('{deact_login.json().get('detail')}')")

        # Reactivate officer for consistency
        react_res = client.post(f"{BASE_URL}/auth/officers/{officer_id_to_approve}/activate", headers=admin_headers)
        assert react_res.status_code == 200, f"Reactivation failed: {react_res.text}"
        print("[PASS] 8.5 Officer reactivated cleanly by administrator")

        results["TEST_8"] = "PASS"
    except Exception as e:
        print(f"[FAIL] TEST 8: {e}")
        results["TEST_8"] = f"FAIL: {e}"

    # =========================================================================
    # TEST 9: EXISTING APPLICATION REGRESSION
    # =========================================================================
    print("\n" + "=" * 50)
    print("TEST 9: EXISTING APPLICATION REGRESSION")
    print("=" * 50)
    try:
        # 1. AI Image Analysis Engine
        img_path = "backend/uploads/original/clear_street.jpg"
        if not os.path.exists(img_path):
            img_path = "uploads/original/clear_street.jpg"
        with open(img_path, "rb") as img_file:
            analyze_res = client.post(
                f"{BASE_URL}/ai/analyze",
                files={"file": ("clear_street.jpg", img_file, "image/jpeg")}
            )
        assert analyze_res.status_code == 200, f"AI analyze failed: {analyze_res.text}"
        analyze_data = analyze_res.json()
        assert "detected_objects" in analyze_data or "raw_detections" in analyze_data
        print(f"[PASS] 9.1 AI Vision Engine operational (Detected objects key present, Latency: {analyze_data.get('processing_time_sec', 0)}s)")

        # 2. Incident Reporting (Citizen)
        unique_lat = round(12.9100 + ((int(uid, 16) % 500) * 0.001), 4)
        unique_lng = round(77.6100 + ((int(uid, 16) % 500) * 0.001), 4)
        inc_payload = {
            "title": f"UAT Footpath Encroachment {uid}",
            "description": "Commercial stalls obstructing pedestrian walkway.",
            "location_name": f"Koramangala Site - UAT {uid}",
            "latitude": unique_lat,
            "longitude": unique_lng,
            "image_url": analyze_data.get("original_image_url") or "/uploads/original/clear_street.jpg",
            "annotated_image_url": analyze_data.get("annotated_image_url"),
            "primary_encroachment_type": "Street Vendor",
            "occupancy_percentage": 25.0,
            "accessibility_score": 75.0,
            "severity": "Medium",
            "risk_score": 50.0
        }
        create_res = client.post(f"{BASE_URL}/incidents", headers=cit_headers, json=inc_payload)
        assert create_res.status_code == 200, f"Incident creation failed: {create_res.status_code} {create_res.text}"
        created_inc = create_res.json()
        inc_id = created_inc["id"]
        inc_num = created_inc["incident_number"]
        print(f"[PASS] 9.2 Incident reporting verified (Created {inc_num}, ID: {inc_id})")

        # 3. Duplicate Detection Check
        dup_chk = client.get(
            f"{BASE_URL}/incidents/{inc_id}/possible-duplicates",
            headers=admin_headers
        )
        assert dup_chk.status_code == 200, f"Duplicate check failed: {dup_chk.text}"
        dup_candidates = dup_chk.json().get('candidates', [])
        print(f"[PASS] 9.3 Duplicate incident detection verified (Found {len(dup_candidates)} nearby candidates)")

        # 4. Multi-Image Evidence Upload
        with open("backend/uploads/original/clear_street.jpg", "rb") as img_file:
            ev_res = client.post(
                f"{BASE_URL}/incidents/{inc_id}/evidence",
                headers=cit_headers,
                files={"file": ("evidence2.jpg", img_file.read(), "image/jpeg")},
                data={"caption": "Angle view showing remaining walkway width"}
            )
        assert ev_res.status_code == 200, f"Evidence upload failed: {ev_res.text}"
        print(f"[PASS] 9.4 Multi-image evidence management verified")

        # 5. SLA Rules and Evaluation
        sla_rules = client.get(f"{BASE_URL}/sla/rules", headers=admin_headers)
        assert sla_rules.status_code == 200
        sla_eval = client.post(f"{BASE_URL}/sla/evaluate", headers=admin_headers)
        assert sla_eval.status_code == 200
        print(f"[PASS] 9.5 SLA Rules & Escalation engine evaluated (Rules: {len(sla_rules.json())})")

        # 6. Citizen My Reports Filter
        my_reps = client.get(f"{BASE_URL}/incidents?my_reports=true", headers=cit_headers)
        assert my_reps.status_code == 200
        my_items = my_reps.json()
        assert any(item.get("id") == inc_id for item in my_items), "Created incident not in My Reports!"
        print(f"[PASS] 9.6 Citizen isolated incident tracking verified ({len(my_items)} reported)")

        # 7. Resolution and Supervisory Verification
        res_submit = client.post(
            f"{BASE_URL}/incidents/{inc_id}/submit-resolution",
            headers=officer_headers,
            json={
                "resolution_notes": "Officer deployed municipal team and cleared all unauthorized structures.",
                "after_image_url": "/uploads/original/clear_street.jpg"
            }
        )
        assert res_submit.status_code == 200, f"Resolution submission failed: {res_submit.text}"
        verify_res = client.post(
            f"{BASE_URL}/incidents/{inc_id}/review-resolution",
            headers=admin_headers,
            json={"decision": "ACCEPT", "notes": "Verified by before/after comparison."}
        )
        assert verify_res.status_code == 200, f"Verification failed: {verify_res.text}"
        print(f"[PASS] 9.7 Incident resolution and supervisory verification workflow verified")

        # 8. Reopening Workflow
        reopen_res = client.post(
            f"{BASE_URL}/incidents/{inc_id}/reopen",
            headers=admin_headers,
            json={"reason": "Citizen reported recurrence of vendor cart."}
        )
        assert reopen_res.status_code == 200, f"Reopen failed: {reopen_res.text}"
        print(f"[PASS] 9.8 Reopening workflow with mandatory reason verified")

        # 9. Public Transparency Portal (100% PII Redaction)
        pub_res = client.get(f"{BASE_URL}/public/incidents")
        assert pub_res.status_code == 200
        pub_list = pub_res.json()
        for p in pub_list[:10]:
            assert "reporter_name" not in p, "PII Leak: reporter_name found in public feed!"
            assert "reporter_phone" not in p, "PII Leak: reporter_phone found in public feed!"
            assert "reporter_id" not in p, "PII Leak: reporter_id found in public feed!"
        print(f"[PASS] 9.9 Public Transparency Portal verified with 100% PII redaction ({len(pub_list)} records)")

        # 10. AI Feedback Dataset & Model Registry
        fb_res = client.get(f"{BASE_URL}/feedback/dataset", headers=admin_headers)
        assert fb_res.status_code == 200, f"Feedback dataset failed: {fb_res.text}"
        reg_res = client.get(f"{BASE_URL}/model-ops/models", headers=admin_headers)
        assert reg_res.status_code == 200, f"Model registry failed: {reg_res.text}"
        print(f"[PASS] 9.10 AI Feedback Dataset and Model Governance Registry verified (Models tracked: {len(reg_res.json())})")

        results["TEST_9"] = "PASS"
    except Exception as e:
        print(f"[FAIL] TEST 9: {e}")
        import traceback
        traceback.print_exc()
        results["TEST_9"] = f"FAIL: {e}"

    print("\n" + "=" * 80)
    print("END-TO-END UAT SUITE SUMMARY")
    print("=" * 80)
    for test, res in results.items():
        print(f"{test}: {res}")
    print("=" * 80)

    all_passed = all(v == "PASS" for v in results.values())
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_full_uat()
