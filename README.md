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

## Level 1 Data Flow Diagram
![Level 1 DFD](docs\images\level1dfd.png)

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