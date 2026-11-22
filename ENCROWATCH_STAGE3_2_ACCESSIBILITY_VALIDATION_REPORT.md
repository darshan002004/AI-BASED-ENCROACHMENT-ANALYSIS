# EncroWatch AI — Stage 3.2: Physical Accessibility Evidence and Validation Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Audit Purpose:** Evidentiary Grounding Audit of the 50 Physical Accessibility Measurement Stations  
**Status Classification Standard:** `PREPARED (Station Network Formatted / In-Situ Logs Pending)`

---

## 1. Executive Validation Verdict

An evidentiary audit was conducted across all 50 entries in [`ENCROWATCH_STAGE3_2_ACCESSIBILITY_MEASUREMENTS.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_STAGE3_2_ACCESSIBILITY_MEASUREMENTS.csv).

```
+----------------------------------------------------------------------------------------------------+
|                                    ACCESSIBILITY AUDIT SUMMARY                                     |
+-----------------------------------+--------------------+--------------------+----------------------+
| Audit Dimension                   | Target Standard    | Observed Status    | Evidentiary Verdict  |
+-----------------------------------+--------------------+--------------------+----------------------+
| Measurement Network Coverage      | 50 Stations (W1-4) | 50 Stations Mapped | PREPARED (Network OK)|
| Optical Laser Specifications      | Bosch GLM 50-27 CG | Documented ISO Cert| PREPARED (Spec OK)   |
| Non-Double-Counting Logic         | Lateral Interval U | Implemented in Py  | VERIFIED (Math OK)   |
| In-Situ Laser Survey Timestamps   | 50 Timestamps      | 0 Logged           | PENDING_FIELD_SURVEY |
| In-Situ Surveyor Sign-off Logs    | 50 Signatures      | 0 Logged           | PENDING_FIELD_SURVEY |
| In-Situ Photographic Proofs       | 50 Photos          | 0 Photos           | PENDING_PHOTO_INTAKE |
| Statutory Regulatory Compliance   | Empirical Evidence | Model Projections  | NOT_VERIFIABLE_EMP.  |
+-----------------------------------+--------------------+--------------------+----------------------+
```

> [!CAUTION]
> **Academic Integrity Ruling:** The 50 rows in the accessibility register represent **pre-survey corridor baseline models** with calibrated instrument specifications. In strict accordance with academic ethics, they are **not claimed as empirical field survey findings** until physical laser distance measurements and field photographs are gathered on-site in Bengaluru.

---

## 2. Ward-by-Ward Station Distribution

```
+-----------------------+---------------------+-------------------+---------------------+------------+
| Ward ID               | Primary Corridor    | Station Count     | Chainage Range      | Partition  |
+-----------------------+---------------------+-------------------+---------------------+------------+
| Ward 1 (East)         | MG Rd / Brigade Rd  | 15 Stations       | Sta 0+040m - 0+630m | Train      |
| Ward 2 (East)         | Indiranagar 100ft Rd| 15 Stations       | Sta 0+080m - 1+200m | Train      |
| Ward 3 (South-East)   | Koramangala 80ft Rd | 10 Stations       | Sta 0+060m - 0+780m | Validation |
| Ward 4 (South)        | BTM Layout 2nd Stage| 10 Stations       | Sta 0+050m - 0+440m | Quarantined|
+-----------------------+---------------------+-------------------+---------------------+------------+
```

- Every station has a designated corridor chainage, anchor waypoint coordinates, nominal corridor width ($W_{\text{nom}}$), and dominant obstacle occupancy model ($W_{\text{obs}}$).
- The measurement methodology is operational at [`scripts/accessibility/accessibility_calculator.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/accessibility/accessibility_calculator.py).
