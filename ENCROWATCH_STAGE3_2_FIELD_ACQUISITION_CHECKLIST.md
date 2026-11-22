# EncroWatch AI — Stage 3.2: Actionable Field Acquisition Checklist

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Target Region:** Bruhat Bengaluru Mahanagara Palike (BBMP) Wards 1 to 4  
**Status Classification Standard:** `PREPARED (Ready for Field Deployment)`

---

## 1. Pre-Fieldwork Equipment and Calibration Protocol

Before deploying to survey corridors in Bengaluru, field researchers must complete and check all items below:

```
[ ] 1. Optical Laser Distance Meter Calibration:
    - Instrument: Bosch GLM 50-27 CG Professional Laser Measure.
    - Verified ISO 16331-1 accuracy rating: +/- 1.5 mm.
    - Factory calibration certificate verified and logged.
    - Fresh lithium batteries installed; target plate clean and free of dirt.

[ ] 2. Handheld Gimbal & Camera Setup:
    - 3-axis motorized gimbal (DJI Osmo Mobile or equivalent) balanced and calibrated.
    - Primary sensor: Minimum 1080p (1920x1080) at 30 fps, optical image stabilization.
    - Camera geometry verified: Height: 1.40 - 1.60 m (eye level); Downward pitch: 15 to 25 degrees.
    - Storage media: Minimum 128 GB high-speed U3/V30 MicroSD card formatted.

[ ] 3. Administrative and Ethics Clearances:
    - Academic research credentials and institutional authorization letter carried.
    - Emergency contact numbers for local municipal ward offices (BBMP) documented.
```

---

## 2. In-Field Data Collection Workflow

Follow this systematic procedure at each designated street segment:

```
+----------------------------------------------------------------------------------------------------+
|                                    IN-FIELD EXECUTION PROTOCOL                                     |
+----+-----------------------+-----------------------------------------------------------------------+
|Step| Activity              | Operational Instructions                                              |
+----+-----------------------+-----------------------------------------------------------------------+
| 1  | Station Navigation    | Navigate to designated corridor station waypoint (e.g., ACC_MSR_001).  |
| 2  | Physical Laser Measure| Mount laser measure against building facade / boundary wall:          |
|    |                       | a. Measure total corridor width to outer curb edge (W_nom).           |
|    |                       | b. Measure lateral footprint width of encroaching obstacle (W_obs).   |
|    |                       | c. Verify remaining clear walking width (W_clear = W_nom - W_obs).    |
| 3  | Measurement Log Entry | Record W_nom, W_obs, W_clear, obstacle class, and timestamp.          |
| 4  | Ground-Truth Photo    | Capture high-resolution reference photo from eye level (1.5 m).        |
| 5  | Video Sequence Walk   | Record continuous 15-30s smooth gimbal walk along corridor vanishing  |
|    |                       | line at normal walking pace (approx. 1.0 m/s).                        |
| 6  | Station Progression   | Advance 50-100 metres along corridor to next designated station.      |
+----+-----------------------+-----------------------------------------------------------------------+
```

---

## 3. Post-Fieldwork Ingestion & Quality Control Protocol

Upon returning from field surveys, execute the automated ingestion pipeline:

```powershell
# In C:\Users\Darshan B\.gemini\antigravity\scratch\encrowatch-ai:
# 1. Deposit raw field images into staging:
Copy-Item "E:\Field_DCIM\*.jpg" "dataset\staging\"

# 2. Run automated intake manager (verifies decodability, SHA-256, and applies PII blur):
& ".\.venv\Scripts\python.exe" "scripts\dataset_inspection\field_data_intake_manager.py"

# 3. Inspect blurred outputs in dataset/privacy_processed/
# 4. Senior reviewer confirms PII removal, promoting assets to dataset/verified/
```

- **Status:** All protocols, checklists, and directory trees are `PREPARED`. Physical execution remains `PENDING` until human fieldwork is completed.
