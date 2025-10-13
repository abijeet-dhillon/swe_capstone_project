# Features Proposal for Project Option: Mining Digital Work Artifacts

**Team Number:** 14  
**Team Members:** Tahsin Jawwad, Abijeet Dhillon, Abdur Rehman, Abhinav Malik, Kaiden Merchant, Misha Gavura

---

## 1. Project Scope and Usage Scenario
Creators (graduating students or early professionals) want a privacy-first way to scan selected folders on their own machines to mine digital work artifacts (code repositories, documents, slides, and media/design files) and produce highlights and portfolio summaries; Administrators (the local machine owner, often the same person) configure and consent to scanning policies such as allowlists/denylists and redaction, while Reviewers (instructors, mentors, hiring managers) never access raw files but consume exported summaries (JSON/CSV/PDF) produced by the system. The typical flow is that a Creator configures a scan, the system parses and normalizes artifact metadata locally, computes insights such as contribution timelines and document activity, stores them locally, and then the Creator exports a concise report for Reviewers.

---

## 2. Proposed Solution
We will implement a local-first pipeline with three components: (1) a Scanner that enumerates files from user-approved folders and detects types; (2) Adapters for key artifact classes (Git repositories via GitPython/pydriller; Office/PDF via `python-docx`/`python-pptx`/`pdfminer`; basic media/design metadata via `ffprobe` or equivalent); and (3) a FastAPI service that exposes REST endpoints for artifacts and insights. Processing and storage remain local by default to protect privacy, and the API will be consumed by a dashboard in Term 2.

Our value proposition is a privacy-first, testable, and extensible architecture that surfaces meaningful signals (commit velocity, project timelines, document activity) in a deterministic way; compared to other teams, we emphasize: (a) a plug-in adapter interface that makes file-type support straightforward to extend, (b) robust PII redaction before storage, and (c) a full requirements→tests traceability matrix to ensure verifiability from the outset.

---

## 3. Use Cases

### **Use Case 1: Give Consent for Data Access**
- **Primary actor:** User / Administrator  
- **Description:** Obtain explicit consent before accessing or analyzing any files.  
- **Precondition:** Application is launched.  
- **Postcondition:** Consent preference is securely stored in configuration.  
- **Main Scenario:**  
  1. User or Administrator opens the application.  
  2. System displays data access consent message.  
  3. User reviews and accepts or declines consent.  
  4. If accepted, consent is stored in local configuration.  
- **Extensions:**  
  - Consent declined → System halts further actions.  
  - Consent record missing → System prompts for authorization again.  

---

### **Use Case 2: Upload & Validate ZIP Folder**
- **Primary actor:** User  
- **Description:** Upload a zipped folder containing nested project files for processing.  
- **Precondition:** Valid user consent exists.  
- **Postcondition:** ZIP folder is validated and ready for parsing.  
- **Main Scenario:**  
  1. User selects ZIP file.  
  2. System validates the format and checks for corruption.  
  3. System extracts contents and prepares data for analysis.  
- **Extensions:**  
  - Invalid file format → System displays an error.  
  - Corrupted ZIP → User is prompted to re-upload.  

---

### **Use Case 3: Request Permission for External Services (LLM)**
- **Primary actor:** User  
- **Description:** Request explicit user permission to use an external AI (LLM) for enhanced analysis.  
- **Precondition:** Valid ZIP folder has been uploaded.  
- **Postcondition:** User’s permission for external data processing is stored.  
- **Main Scenario:**  
  1. System prompts user for LLM usage consent.  
  2. User is informed of privacy implications.  
  3. User allows or denies access.  
  4. System stores this preference in configuration.  
- **Extensions:**  
  - Permission denied → System performs local-only analysis.  

---

### **Use Case 4: Run Analysis (Local or LLM-Assisted)**
- **Primary actor:** User  
- **Description:** Analyze uploaded files locally or using an LLM, depending on granted permissions.  
- **Precondition:** ZIP folder validated and permissions recorded.  
- **Postcondition:** Analysis metrics and intermediate results generated.  
- **Main Scenario:**  
  1. User initiates analysis.  
  2. System processes files and applies parsing adapters.  
  3. External LLM/API assists if permission granted.  
  4. Results are stored temporarily.  
- **Extensions:**  
  - Timeout on large files → Skipped with a warning.  
  - LLM unreachable → Fallback to local analysis.  

---

### **Use Case 5: Extract Key Metrics & Skills**
- **Primary actor:** User  
- **Description:** Identify project metrics and skills from analyzed artifacts.  
- **Precondition:** Analysis has been completed successfully.  
- **Postcondition:** Extracted information saved to project record.  
- **Main Scenario:**  
  1. System identifies project type and structure.  
  2. Detects programming languages, frameworks, and key metrics (duration, frequency).  
  3. Extracts skill insights from artifacts.  
  4. Stores extracted data for future retrieval.  
- **Extensions:**  
  - Missing metadata → System estimates based on available data.  

---

### **Use Case 6: Store Configurations & Project Data**
- **Primary actor:** User / Administrator  
- **Description:** Save configurations, permissions, and analyzed project data into persistent storage.  
- **Precondition:** Analysis or configuration data exists.  
- **Postcondition:** Data saved successfully in local database.  
- **Main Scenario:**  
  1. System saves configurations and generated insights.  
  2. Administrator manages privacy and retention settings.  
- **Extensions:**  
  - Storage error → System retries or logs the issue.  

---

### **Use Case 7: Delete Insights Safely**
- **Primary actor:** Administrator  
- **Description:** Delete stored analysis results without affecting shared or dependent data.  
- **Precondition:** Data to delete exists in the system.  
- **Postcondition:** Target data is removed securely.  
- **Main Scenario:**  
  1. Administrator requests deletion of stored insights.  
  2. System checks dependencies and confirms deletion.  
  3. Data removed securely.  
- **Extensions:**  
  - Shared data found → System preserves shared records and logs the action.  

---

### **Use Case 8: Retrieve Stored Portfolio / Resume Info**
- **Primary actor:** User  
- **Description:** Retrieve previously stored project and résumé information from the local database.  
- **Precondition:** Past analysis and data exist.  
- **Postcondition:** Data fetched and ready for output generation.  
- **Main Scenario:**  
  1. User requests previously stored portfolio data.  
  2. System retrieves summary information from storage.  
  3. Data displayed or formatted for export.  
- **Extensions:**  
  - No stored data → System prompts to run a new analysis.  

---

### **Use Case 9: Generate Text-Based Output (Résumé / Portfolio Info)**
- **Primary actor:** User / Reviewer  
- **Description:** Produce text-based summaries (JSON, CSV, or plain text) representing portfolio and résumé insights.  
- **Precondition:** Analyzed and stored project data exists.  
- **Postcondition:** Output file generated and ready for sharing.  
- **Main Scenario:**  
  1. User selects output type and scope.  
  2. System generates text-based summary of insights.  
  3. Output file created locally.  
  4. Reviewer opens the exported file for review.  
- **Extensions:**  
  - Invalid path or permission denied → System requests new save location.  

---



![UML Diagram](./revised-uml-diagram.png)




---




## 4. Requirements, Testing, Requirement Verification

**Technology stack & test framework:** Python 3.11, FastAPI, GitPython/pydriller, `python-docx`/`python-pptx`/`pdfminer`, optional `ffprobe`; testing with `pytest` (unit/integration), FastAPI `TestClient`, coverage via `pytest-cov`, GitHub Actions CI.

## Requirements, Testing, and Verification

### Requirements Table

| Requirement | Description | Test Cases | Who | H/M/E |
|---|---|---|---|---|
| **R1 Consent & Configuration** | User must provide explicit consent and configure data access settings | **Positive:** TC1.1 User grants consent → stored securely.<br>TC1.2 Config saved correctly.<br>**Negative:** TC1.3 Consent declined → processing blocked.<br>TC1.4 Missing config → prompt again. | **Tahsin Jawwad** | M |
| **R2 ZIP Validation & Parsing** | System must validate and extract contents from uploaded ZIP | **Positive:** TC2.1 Valid ZIP → extracted successfully.<br>TC2.2 Nested folders handled.<br>**Negative:** TC2.3 Wrong format → error shown.<br>TC2.4 Corrupted file skipped. | **Misha** | M |
| **R3 External LLM Permission** | Request and store user permission for external service (LLM/API) use | **Positive:** TC3.1 Consent accepted → flag stored.<br>TC3.2 User informed of data privacy.<br>**Negative:** TC3.3 Denied → local-only mode.<br>TC3.4 No response → defaults to deny. | **Abdur Rehman** | M |
| **R4 Local & LLM-Assisted Analysis** | Analyze data locally or via LLM if permitted | **Positive:** TC4.1 Local parsing works.<br>TC4.2 LLM request handled securely.<br>**Negative:** TC4.3 Timeout → skipped with warning.<br>TC4.4 LLM unavailable → fallback to local. | **Abijeet Dhillon** | H |
| **R5 Metrics & Skill Extraction** | Extract project type, key metrics, and inferred skills | **Positive:** TC5.1 Correct metrics computed.<br>TC5.2 Skill keywords identified.<br>**Negative:** TC5.3 Missing metadata handled.<br>TC5.4 Unreadable file skipped. | **Abhinav Malik** | M |
| **R6 Storage & Persistence** | Persist user config, consent, and analysis outputs | **Positive:** TC6.1 Insert and retrieve data.<br>TC6.2 Update works without loss.<br>**Negative:** TC6.3 Invalid record rejected.<br>TC6.4 Storage error logged. | **Kaiden Merchant** | M |
| **R7 Deletion & Privacy Controls** | Delete or purge stored insights safely | **Positive:** TC7.1 Valid delete → data removed.<br>TC7.2 Shared data preserved.<br>**Negative:** TC7.3 Missing data → graceful fail.<br>TC7.4 Unauthorized request denied. | **Abdur Rehman** | M |
| **R8 Retrieval & Output Generation** | Retrieve previously generated portfolio/résumé data | **Positive:** TC8.1 Fetch previous insights.<br>TC8.2 Retrieve historical summaries.<br>**Negative:** TC8.3 Empty DB → prompt new scan.<br>TC8.4 Missing entry handled. | **Tahsin Jawwad** | M |
| **R9 Export Text-Based Output** | Export portfolio/résumé insights in text, JSON, or CSV format | **Positive:** TC9.1 JSON export valid.<br>TC9.2 CSV opens correctly.<br>**Negative:** TC9.3 Invalid path → error.<br>TC9.4 File locked → retry prompt. | **Misha** | E |

---

### Workload Summary

- **Tahsin Jawwad** → R1 (M), R8 (M) → Consent + retrieval  
- **Abijeet Dhillon** → R4 (H) → Local + LLM analysis  
- **Misha** → R2 (M), R9 (E) → ZIP parsing + export  
- **Abhinav Malik** → R5 (M) → Metrics and skill extraction  
- **Kaiden Merchant** → R6 (M) → Storage and persistence  
- **Abdur Rehman** → R3 (M), R7 (M) → External permission + privacy/deletion  

---
