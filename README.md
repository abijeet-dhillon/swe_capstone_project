[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=20510468&assignment_repo_type=AssignmentRepo)
# Project-Starter
Please use the provided folder structure for your project. You are free to organize any additional internal folder structure as required by the project. 

```
.
├── docs                    # Documentation files
│   ├── contract            # Team contract
│   ├── proposal            # Project proposal 
│   ├── design              # UI mocks
│   ├── minutes             # Minutes from team meetings
│   ├── logs                # Team and individual Logs
│   └── ...          
├── src                     # Source files (alternatively `app`)
├── tests                   # Automated tests 
├── utils                   # Utility files
└── README.md
```

Please use a branching workflow, and once an item is ready, do remember to issue a PR, review, and merge it into the master branch.
Be sure to keep your docs and README.md up-to-date.

# Project Diagrams
## System Architecture Diagram
![System Architecture](docs/images/revised-uml-diagram.png)

The **System Architecture Diagram** above represents the core workflow of the *Mining Digital Work Artifacts System*, showing the interaction between users, administrators, reviewers, and external services.  

### Overview  
The system facilitates the secure extraction of professional insights (résumé or portfolio information) from digital work artifacts. It emphasizes **data privacy, consent management, and controlled use of external AI services (LLMs)**.  

### Main Components  
1. **Actors**
   - **Administrator** – Manages data access permissions and overall system governance.  
   - **User** – Provides data (e.g., ZIP folders), grants permissions, and retrieves results.  
   - **Reviewer** – Evaluates generated outputs for accuracy and relevance.  
   - **External LLM/API** – Supports AI-assisted analysis when user consent allows.  

2. **Core Processes**
   - **Give Consent for Data Access** – Ensures user and admin authorization before any processing.  
   - **Upload & Validate ZIP Folder** – Users upload their work data, which the system validates.  
   - **Request Permission for External Services (LLM)** – Manages consent for sending data to external AI systems.  
   - **Run Analysis (Local or LLM-Assisted)** – Executes data mining to extract metrics and skills.  
   - **Extract Key Metrics & Skills** – Summarizes user competencies and project patterns.  
   - **Store Configurations & Project Data** – Saves extracted insights, maintaining confidentiality.  
   - **Retrieve Stored Portfolio / Résumé Info** – Allows users or reviewers to fetch stored insights.  
   - **Generate Text-Based Output** – Produces structured résumé or portfolio summaries.  
   - **Delete Insights Safely** – Ensures data can be removed securely without leaving residual traces.  

3. **Data Flow**
   - **Inputs:** User uploads (ZIP files) and consent records.  
   - **Processing:** Validation → Analysis → Storage → Output generation.  
   - **Outputs:** Structured resume/portfolio insights.  
   - **Feedback Loop:** Reviewers and users can trigger re-analysis or deletion requests.  

This architecture ensures transparency, modularity, and privacy compliance while leveraging AI tools responsibly to analyze digital work artifacts.

## Level 1 Data Flow Diagram
![Level 1 DFD](docs/images/level1dfd.png)

The link for the same DFD can be viewed using this [link](https://lucid.app/lucidchart/c9654f3d-90ee-4b90-83d7-652ac1448dad/edit?viewport_loc=-76%2C-92%2C2911%2C1466%2C6~KY3uEuKYee&invitationId=inv_5a51ab76-9aa7-4549-b897-4f521982137b).

### Explanation:
The Level-1 DFD shows the internal data flows and subprocesses within the **Mining Digital Work Artifacts** system.  
It highlights how user inputs (ZIP folders and consent) move through validation, analysis, and reporting to generate résumé and portfolio insights, while maintaining user privacy and configurability. Here is an explanation for the main components of the diagram:

#### 1. **User**
Interacts with the system by:
- Uploading ZIP folder/path references  
- Granting or denying data access/LLM permissions  
- Requesting résumé or portfolio data  
- Deleting stored insights  

#### 2. **ZIP Upload / Validator**
Validates the uploaded ZIP.  
- If valid, it passes content to `Folder Parser`  
- Otherwise, it returns an error  

#### 3. **Folder Parser**
Unpacks the ZIP and normalizes artifacts into structured metadata.

#### 4. **Consent and Configuration**
Captures user consent and configuration settings (privacy preferences, LLM usage) and updates **D1 User Config**.

#### 5. **LLM / Local Analyser**
Analyzes normalized data:
- Checks LLM permissions and uses LLMs if permitted  
- Falls back to local analysis otherwise  
- Extracts project metrics, extrapolation of individual contributions, timelines, and skills  
- Stores results in **D2 Project Database**

#### 6. **Summary / Portfolio Generator**
Generates summarized project insights, ranked contributions, and résumé-ready highlights.

#### 7. **Data Retrieval**
Fetches stored résumé/portfolio data from the project database when requested.

#### 8. **Delete Insights with Validation**
Processes deletion requests and ensures shared data across reports is preserved.

#### Data Stores
- **D1 User Config** → stores consent and user preferences  
- **D2 Project Database** → stores extracted project insights and summaries  