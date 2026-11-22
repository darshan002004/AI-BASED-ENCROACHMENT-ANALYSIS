import sys
import httpx

BASE_URL = "http://127.0.0.1:8000/api"

def test_roles_and_endpoints():
    client = httpx.Client(timeout=10.0)
    print("==================================================")
    print("Testing EncroWatch AI Role-Based Authentication & Authorization")
    print("==================================================")

    # 1. Health check
    res = client.get(f"{BASE_URL}/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    print("[PASS] 1. Backend health check: OK")

    # 2. Authenticate Admin
    admin_res = client.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@encrowatch.ai", "password": "admin123"}
    )
    assert admin_res.status_code == 200, f"Admin login failed: {admin_res.text}"
    admin_data = admin_res.json()
    admin_token = admin_data["access_token"]
    assert admin_data["user"]["role"] == "admin", f"Expected admin role, got {admin_data['user']['role']}"
    print(f"[PASS] 2. Admin login successful. Role: '{admin_data['user']['role']}' (Email: {admin_data['user']['email']})")

    # 3. Authenticate Officer
    officer_res = client.post(
        f"{BASE_URL}/auth/login",
        json={"email": "officer@encrowatch.ai", "password": "officer123"}
    )
    assert officer_res.status_code == 200, f"Officer login failed: {officer_res.text}"
    officer_data = officer_res.json()
    officer_token = officer_data["access_token"]
    assert officer_data["user"]["role"] == "officer", f"Expected officer role, got {officer_data['user']['role']}"
    print(f"[PASS] 3. Officer login successful. Role: '{officer_data['user']['role']}' (Email: {officer_data['user']['email']})")

    # 4. Authenticate Citizen
    citizen_res = client.post(
        f"{BASE_URL}/auth/login",
        json={"email": "citizen@encrowatch.ai", "password": "citizen123"}
    )
    assert citizen_res.status_code == 200, f"Citizen login failed: {citizen_res.text}"
    citizen_data = citizen_res.json()
    citizen_token = citizen_data["access_token"]
    assert citizen_data["user"]["role"] == "citizen", f"Expected citizen role, got {citizen_data['user']['role']}"
    print(f"[PASS] 4. Citizen login successful. Role: '{citizen_data['user']['role']}' (Email: {citizen_data['user']['email']})")

    # 5. Invalid credentials - must return 401 Unauthorized, never default to admin
    bad_res = client.post(
        f"{BASE_URL}/auth/login",
        json={"email": "invalid@encrowatch.ai", "password": "wrongpassword"}
    )
    assert bad_res.status_code == 401, f"Expected 401, got {bad_res.status_code}"
    print("[PASS] 5. Invalid login correctly rejected with 401 Unauthorized (no default fallback)")

    # 6. Test GET /auth/me for each role
    for name, tok, expected_role in [
        ("Admin", admin_token, "admin"),
        ("Officer", officer_token, "officer"),
        ("Citizen", citizen_token, "citizen"),
    ]:
        me_res = client.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {tok}"}
        )
        assert me_res.status_code == 200, f"/auth/me failed for {name}"
        me_role = me_res.json().get("role")
        assert me_role == expected_role, f"/auth/me for {name} returned {me_role}, expected {expected_role}"
        print(f"[PASS] 6. /auth/me for {name} verified: role='{me_role}'")

    # 7. Test User Management endpoint authorization (/auth/users)
    # Admin: 200 OK
    users_admin = client.get(
        f"{BASE_URL}/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert users_admin.status_code == 200, f"Admin failed to access /auth/users: {users_admin.status_code}"
    print(f"[PASS] 7a. Admin authorized for /auth/users (HTTP 200, {len(users_admin.json())} users listed)")

    # Officer: 403 Forbidden
    users_officer = client.get(
        f"{BASE_URL}/auth/users",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert users_officer.status_code == 403, f"Officer was not forbidden from /auth/users: {users_officer.status_code}"
    print(f"[PASS] 7b. Officer correctly forbidden from /auth/users (HTTP 403 Forbidden)")

    # Citizen: 403 Forbidden
    users_citizen = client.get(
        f"{BASE_URL}/auth/users",
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    assert users_citizen.status_code == 403, f"Citizen was not forbidden from /auth/users: {users_citizen.status_code}"
    print(f"[PASS] 7c. Citizen correctly forbidden from /auth/users (HTTP 403 Forbidden)")

    # 8. Test Officer Roster endpoint authorization (/auth/officers)
    # Admin: 200 OK
    off_admin = client.get(
        f"{BASE_URL}/auth/officers",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert off_admin.status_code == 200
    print(f"[PASS] 8a. Admin authorized for /auth/officers (HTTP 200, {len(off_admin.json())} officers)")

    # Officer: 200 OK
    off_officer = client.get(
        f"{BASE_URL}/auth/officers",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert off_officer.status_code == 200
    print(f"[PASS] 8b. Officer authorized for /auth/officers (HTTP 200)")

    # Citizen: 403 Forbidden
    off_citizen = client.get(
        f"{BASE_URL}/auth/officers",
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    assert off_citizen.status_code == 403
    print(f"[PASS] 8c. Citizen correctly forbidden from /auth/officers (HTTP 403 Forbidden)")

    # 9. Test Audit Logs endpoint authorization (/audit/logs)
    audit_admin = client.get(
        f"{BASE_URL}/audit/logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert audit_admin.status_code == 200
    print(f"[PASS] 9a. Admin authorized for /audit/logs (HTTP 200)")

    audit_officer = client.get(
        f"{BASE_URL}/audit/logs",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert audit_officer.status_code == 200
    print(f"[PASS] 9b. Officer authorized for /audit/logs (HTTP 200)")

    audit_citizen = client.get(
        f"{BASE_URL}/audit/logs",
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    assert audit_citizen.status_code == 403
    print(f"[PASS] 9c. Citizen correctly forbidden from /audit/logs (HTTP 403 Forbidden)")

    # 10. Test Audit Integrity check (/audit/verify-integrity)
    int_admin = client.get(
        f"{BASE_URL}/audit/verify-integrity",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert int_admin.status_code == 200
    print(f"[PASS] 10a. Admin authorized for cryptographic audit integrity check (HTTP 200)")

    int_officer = client.get(
        f"{BASE_URL}/audit/verify-integrity",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert int_officer.status_code == 403
    print(f"[PASS] 10b. Officer correctly forbidden from audit integrity check (HTTP 403 Forbidden)")

    # 11. Test SLA Rules update authorization (/sla/rules)
    sla_officer = client.put(
        f"{BASE_URL}/sla/rules",
        json={"rules": []},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert sla_officer.status_code == 403
    print(f"[PASS] 11a. Officer correctly forbidden from updating SLA rules (HTTP 403 Forbidden)")

    sla_citizen = client.put(
        f"{BASE_URL}/sla/rules",
        json={"rules": []},
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    assert sla_citizen.status_code == 403
    print(f"[PASS] 11b. Citizen correctly forbidden from updating SLA rules (HTTP 403 Forbidden)")

    print("\n==================================================")
    print("ALL ROLE-BASED AUTHENTICATION & AUTHORIZATION TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_roles_and_endpoints()
