# Individual Log – Abhinav Malik

## Week 3 – September 15 to September 21

### 1. Type of Tasks Worked On
![Week 3 Task Screenshot](images/week3-abhinavmalik.png)  

---

### 3. Recap of Weekly Goals
This week was mainly focused on early requirement gathering and planning activities. My contributions included:  
- helping define the project requirements and scope  
- reviewing features related to artifact collection and analysis with the team  
- collaborating with group members to finalize the initial requirements document  

---

### 4. Features Owned in Project Plan
- Requirements Documentation  

---

### 5. Tasks from Project Board Associated with These Features
- Project Requirements  

---

### 6. Tasks Completed / In Progress in the Last 2 Weeks
| Task ID | Issue Title          | Status     | Notes |
|---------|----------------------|------------|-------|
| 3       | Project Requirements | Completed  | Drafted and reviewed with team |

---

### 7. Additional Context
N/A


## Week 4 – September 22 to September 28

### 1. Type of Tasks Worked On
![Week 4 Task Screenshot](images/abhinav_week4.png)

---

### 3. Recap of Weekly Goals
This week, the focus shifted to design and proposal activities. My contributions included:  
- collaborating on creating the system architecture diagram  
- contributing to drafting and completing the project proposal  

---

### 4. Features Owned in Project Plan
- System Architecture Diagram  
- Project Proposal  

---

### 5. Tasks from Project Board Associated with These Features
- System Architecture Diagram  
- Project Proposal  

---

### 6. Tasks Completed / In Progress in the Last 2 Weeks
| Task ID | Issue Title              | Status       | Notes |
|---------|--------------------------|--------------|-------|
| 4       | System Architecture      | Completed    | Worked with team to finalize diagram |
| 5       | Project Proposal         | In Progress  | Draft completed, reviewing with team |

---

### 7. Additional Context
N/A  

--- 

## Week 5 – September 29 to October 5

### 1. Type of Tasks Worked On
![Week 5 Task Screenshot](images/week5-abhinavmalik.png)

---

### 3. Recap of Weekly Goals
This week focused on data flow diagrams and system modeling activities. My contributions included:  
- collaborating on creating Level 0 and Level 1 Data Flow Diagrams (DFDs)  
- reviewing and refining the DFDs with the team to ensure logical flow and accuracy  
- discussing with other teams for feedback and improvement  

---

### 4. Features Owned in Project Plan
- Data Flow Diagram  

---

### 5. Tasks from Project Board Associated with These Features
- Data Flow Diagram  

---

### 6. Tasks Completed / In Progress in the Last 2 Weeks
| Task ID | Issue Title          | Status     | Notes |
|---------|----------------------|------------|-------|
| 6       | Data Flow Diagram    | Completed  | Created Level 0 and Level 1 DFDs with team collaboration |

---

### 7. Additional Context
N/A  



## Week 6 – October 6 to October 12

### 1. Type of Tasks Worked On
![Week 6 Task Screenshot](images/week6-log-abhinav.png)

---

### 3. Recap of Weekly Goals
This week was focused on revising and refining the system architecture diagram to align with updated workflow and consent management logic in the Mining Digital Work Artifacts System.  
My contributions included:  
- updating and restructuring the system architecture diagram based on feedback  
- improving clarity in actor interactions (User, Administrator, Reviewer, External LLM/API)  
- aligning data flow with the Level 1 DFD for consistency  
- preparing updated documentation for submission  

---

### 4. Features Owned in Project Plan
- System Architecture Diagram (Revision)  
- Documentation Updates  

---

### 5. Tasks from Project Board Associated with These Features
- System Architecture Revision  
- Documentation Updates  

---

### 6. Tasks Completed / In Progress in the Last 2 Weeks
| Task ID | Issue Title                    | Status      | Notes |
|---------|--------------------------------|-------------|-------|
| 7       | System Architecture Revision   | Completed   | Revised diagram to reflect updated workflow and external service permissions |
| 8       | Documentation Updates          | Completed | Updated README.md and project documentation to include revised architecture |

---

### 7. Additional Context
-   
- 



---
## Week 7 – October 13 to October 19

### 1. Type of Tasks Worked On
![Week 7 Task Screenshot](images/week7-abhinav-tasks.png)
---

### 3. Recap of Weekly Goals
This week focused on developing and testing the consent management functionality for the system.  
My main contributions included:  
- implementing the LLM Consent Manager module to handle user consent for external LLM data access  
- writing and running unit tests to verify consent operations such as grant, revoke, and reset  
- designing the system to be compatible with future modules like directory access consent and external LLM analysis  

---

### 4. Features Owned in Project Plan
- User Consent – External LLM Data Access  
- Consent Management Module  

---

### 5. Tasks from Project Board Associated with These Features
- User Consent – External LLM Data Access (#17)  
- LLM Consent Management Implementation (Internal)  

---

### 6. Tasks Completed / In Progress in the Last 2 Weeks
| Task ID | Issue Title                           | Status       | Notes |
|----------|---------------------------------------|--------------|-------|
| 17       | User Consent – External LLM Data Access | Completed  | Implemented backend LLM consent manager with JSON persistence and test coverage |
| —        | LLM Consent Management Implementation  | Completed    | Added module to handle user opt-in/out consent  |

---

### 7. Additional Context
- All tests for the LLM consent manager passed successfully after debugging one write-handling issue.  
- Code was structured to integrate easily with future directory access consent and external LLM analysis features.  
- Preparing to begin work on the External LLM Analysis module in the next sprint.  
- Continued documenting and refining the module for clarity and maintainability.  


## Week 8 – October 20 to October 26

### 1. Type of Tasks Worked On
![Week 8 Task Screenshot](images/week8-abhinavmalik.png)

---

### 3. Recap of Weekly Goals
This week focused on implementing and testing the Video Analyzer feature, which automates metadata extraction and statistical analysis from local video files and directories.  
My main contributions included:  
- developing the VideoAnalyzer module with methods for analyzing single files and directories  
- implementing detailed metrics aggregation (total duration, average FPS, audio count, etc.)  
- adding colorized CLI output via colorama for improved terminal feedback  
- writing comprehensive automated tests achieving over 95% coverage  
- performing manual validation with real video files to ensure correct metadata extraction  

---

### 4. Features Owned in Project Plan
- Video Analyzer Module  
- Local Video Metrics Extraction  
- Testing and CLI Integration  

---

### 5. Tasks from Project Board Associated with These Features
- local analyzer - video processor  

---

### 6. Tasks Completed 
| Task ID | Issue Title                          | Status      | Notes |
|----------|--------------------------------------|-------------|-------|
| 21       | Local analyzer - video processor           | Completed   | Added functionality to extract metadata and compute collection metrics |


---

### 7. Additional Context
- Ensured compatibility with moviepy and ffmpeg for video processing.  
- Integrated robust error handling for corrupt or unsupported file formats.  
- Verified that all CLI interactions worked across different operating systems (Windows + Git Bash).  
- Documented the full testing process and created a dedicated Testing Guide (VIDEO_ANALYZER_TESTING_GUIDE.md).  

---

### 8. Next Week’s Focus
- Begin integration of Video Analyzer results into the overall artifact collection pipeline.  
- Implement optional JSON export for analyzed results to enable downstream data use.  
- Work on connecting VideoAnalyzer outputs with the Consent Manager to ensure local-only privacy compliance


## Week 9 – October 27 to November 2

### 1. Type of Tasks Worked On
![Week 9 Task Screenshot](images/week9-abhinavmalik.png)

---

### 3. Recap of Weekly Goals
This week focused on extending the Video Analyzer module to support audio transcription and improving system robustness.  
My main contributions included:  
- integrating Whisper-based audio transcription to extract spoken content from video files with audio tracks  
- updating unit tests to validate transcription logic and ensure accurate metadata-to-text pipeline coverage  
- debugging runtime issues related to subprocess handling and ensuring the analyzer gracefully skips missing or invalid configurations  
- verifying real-world test cases using local MP4 and MOV files for full functional validation  

---

### 4. Features Owned in Project Plan
- Video Analyzer – Transcription Extension  
- FFmpeg + Whisper Integration  
- Video Analyzer Unit Tests Update  

---

### 5. Tasks from Project Board Associated with These Features
- Video Analyzer – Transcription and Audio Processing  
- Update Test Suite for VideoAnalyzer  

---

### 6. Tasks Completed / In Progress in the Last 2 Weeks
| Task ID | Issue Title                               | Status       | Notes |
|----------|-------------------------------------------|--------------|-------|
| 92       | local Analyzer – video transcriber | Completed    | Added Whisper model support for speech-to-text transcription |

---

### 7. Additional Context
- Ensured Whisper models (`tiny`, `base`, etc.) run efficiently with automatic error handling for unavailable models.  
- Verified cross-platform setup by documenting FFmpeg installation for Windows, macOS, and Linux users.  
- Updated the project’s `README.md` to include system dependency setup and usage instructions for transcription.  
- Conducted successful end-to-end runs of `video_example_usage.py` to validate real video input, transcription output, and JSON export pipeline.  

---

### 8. Next Week’s Focus
- Begin integrating transcribed text data with the artifact collection and consent validation modules.  
- Work on a method for storing analyzed metadata and transcription results in a structured database 
- Explore how this data layer can connect to the broader artifact analysis pipeline for unified retrieval and reporting.



## Week 10 – November 3 to November 9

### 1. Type of Tasks Worked On
![Week 10 Task Screenshot](images/week10-abhinav-tasks.png)

---

### 3. Recap of Weekly Goals
This week focused on implementing and validating the **Advanced Skill Extractor** for Python files, introducing confidence-based skill scoring and structured JSON output.  
My main contributions included:  
- implementing confidence-based scoring logic using AST-based static analysis  
- integrating evidence-level reasoning (pattern type, location, and confidence) for detected skills  
- extending directory-wide analysis with JSON export support for automated result aggregation  
- performing multiple test iterations to verify accuracy and consistency across diverse Python samples  

---

### 4. Features Owned in Project Plan
- Advanced Skill Extractor (Python)  
- Confidence-Based Skill Scoring  
- JSON Export Integration  

---

### 5. Tasks from Project Board Associated with These Features
- Advanced Skill Extractor Implementation  
- Confidence Score Integration  
- JSON Export for Skill Analysis  

---

### 6. Tasks Completed / In Progress in the Last 2 Weeks
| Task ID | Issue Title                              | Status      | Notes |
|----------|------------------------------------------|-------------|-------|
| 123      | Implement confidence-based evidence scoring for Python in AdvancedSkillExtractor | Completed   | Added AST-driven confidence calculation using detection frequency and pattern context |

---

### 7. Additional Context
- Currently, confidence scoring applies only to Python-based analysis; cross-language support will be added later.  
- Verified single-file and directory analyses using both manual command-line testing and automated pytest validation.  

### 8. Next Week's Focus
- Extend the confidence scoring framework to other languages (Java, C++, JavaScript).
- Add skill category mapping for architecture, performance, and design patterns.
