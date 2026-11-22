import subprocess
import sys

test_files = [
    "backend/test_batch1_upgrades.py",
    "backend/test_batch2_upgrades.py",
    "backend/test_batch3_upgrades.py",
    "backend/test_batch4_upgrades.py",
    "backend/test_batch5_upgrades.py",
    "backend/test_batch5_5_upgrades.py",
    "backend/test_roles_e2e.py",
    "backend/test_officer_registration.py"
]

total_passed = 0
total_failed = 0

print("=" * 60)
print("RUNNING ALL AUTOMATED REGRESSION & ROLE VERIFICATION TESTS")
print("=" * 60)

for tf in test_files:
    if tf.endswith("test_roles_e2e.py") or tf.endswith("test_officer_registration.py"):
        cmd = [sys.executable, tf]
    else:
        cmd = [sys.executable, "-m", "pytest", tf, "-q"]
        
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[PASS] {tf}")
        total_passed += 1
    else:
        print(f"[FAIL] {tf}")
        print(res.stderr or res.stdout)
        total_failed += 1

print("=" * 60)
print(f"SUMMARY: {total_passed}/{len(test_files)} test suites passed, {total_failed} failed")
print("=" * 60)

if total_failed > 0:
    sys.exit(1)
