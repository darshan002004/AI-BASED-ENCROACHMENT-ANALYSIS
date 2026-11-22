# EncroWatch AI — Stage 3.2: Actionable Physical Accessibility Survey Checklist

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Target Scope:** 50 Cross-Sectional Footpath Stations (Bengaluru Wards 1 to 4)  
**Status Classification Standard:** `PREPARED (Ready for Field Deployment)`

---

## 1. Survey Equipment and Tool Setup

Field surveyors must verify and calibrate all instruments prior to departing for the survey corridors:

```
[ ] 1. Laser Distance Meter Check:
    - Model: Bosch GLM 50-27 CG Professional (Green Beam, Bluetooth connectivity).
    - Accuracy: ISO 16331-1 certified (+/- 1.5 mm).
    - Certificate Number: Verified against factory calibration card.
    - Zero-datum reference: Set to rear instrument edge (butt-end reference).

[ ] 2. Rigid Target Plate:
    - Matte red/white target plate used when measuring across open curb edges without a vertical face.

[ ] 3. Survey Logging Terminal:
    - Tablet or mobile device loaded with dataset/measurements/station_survey_form.csv.
```

---

## 2. On-Site Measurement Procedure at Each Station

At each station (`ACC_MSR_001` to `ACC_MSR_050`), execute the 6-step protocol:

```
+----------------------------------------------------------------------------------------------------+
|                                    STATION MEASUREMENT PROTOCOL                                    |
+----+-----------------------+-----------------------------------------------------------------------+
|Step| Operation             | Detailed Instructions                                                 |
+----+-----------------------+-----------------------------------------------------------------------+
| 1  | Station Alignment     | Verify GPS anchor point and station chainage (e.g., Sta 0+120m).      |
| 2  | Nominal Width (W_nom) | Place laser base flush against building wall; beam aimed at curb edge.|
|    |                       | Trigger laser 3 times; record mean reading in metres (e.g., 2.80 m).  |
| 3  | Obstacle Width (W_obs)| Measure lateral extent of obstacle occupying the walkway pavement.   |
| 4  | Clear Width (W_clear) | Verify clear walking width: W_clear = W_nom - W_obs.                  |
| 5  | Surface Condition     | Log paving type: Paver Tiles / Concrete / Asphalt / Broken Slab / Dirt.|
| 6  | Photo Verification    | Capture eye-level (1.5 m) photograph with laser measurement visible.  |
| 7  | Log Sign-Off          | Surveyor signs record: Timestamp, Surveyor ID, Uncertainty (+/-1.5mm).|
+----+-----------------------+-----------------------------------------------------------------------+
```

---

## 3. Data Ingestion Protocol

Upon survey completion:
1. Ingest survey logs into [`ENCROWATCH_STAGE3_2_ACCESSIBILITY_MEASUREMENTS.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_STAGE3_2_ACCESSIBILITY_MEASUREMENTS.csv).
2. Store station reference photos in `dataset/measurements/photos/`.
3. Re-run [`scripts/accessibility/accessibility_calculator.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/accessibility/accessibility_calculator.py) to update statutory compliance flags with empirical field data.
