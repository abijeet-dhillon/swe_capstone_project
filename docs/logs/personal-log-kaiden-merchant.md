# Individual Log - Kaiden Merchant

## TOC

1. [Week 3](#week-3)
1. [Week 4](#week-4)
1. [Week 5](#week-5)
1. [Week 6](#week-6)
1. [Week 7](#week-7)
1. [Week 8](#week-8)
1. [Week 9](#week-9)

## Week 3
This section outlines the individual log for week 3

### September 15 - September 21

### Tasks
![](images/kaiden_week3_tasks.png)

### Weekly Goals

1. My Features: 
    - Discuss the project outline with the team to understand our user base and project's purpose.
    - Develop / refine our project requirements by discussing with other teams and mapping requirements to use cases.

2. Associated Tasks
    - N/A

3. Completed/In-Progress
    - Completed discussions with the team to understand the project.
    - Completed project requirements document.

## Week 4
This section outlines the individual log for week 4

### September 22 - September 28

### Tasks
![](images/kaiden_week4_tasks.png)

### Weekly Goals

1. My Features: 
    - Map requirements to system design components.
    - Build system design architecture diagram.
    - Refine requirements for the project proposal

2. Associated Tasks
    - System Architecture Diagram
    - Project Proposal

3. Completed/In-Progress
    - Completed system architecture diagram with updates from the discussion in class.
    - Completed project proposal.

## Week 5
This section outlines the individual log for week 5

### September 29 - October 5

### Tasks
![](images/kaiden_week5_tasks.png)

### Weekly Goals

1. My Features: 
    - Create DFD (level 0, level 1) diagrams

2. Associated Tasks
    - Data Flow Diagram

3. Completed/In-Progress
    - Completed level 0 diagram 
    - Completed level 1 diagram
    
## Week 6
This section outlines the individual log for week 6

### October 6 - October 12

### Tasks
![](images/kaiden_week6_tasks.png)

### Weekly Goals

1. My Features: 
    - Revise DFD based on new requirements

2. Associated Tasks
    - Data Flow Diagram

3. Completed/In-Progress
    - Completed refactoring of dfd (via new requirements)

## Week 7
This section outlines the individual log for week 7

### October 13 - October 19

### Tasks
![](images/kaiden_week7_tasks.png)

### Weekly Goals

1. My Features: 
    - Update README.md with comprehensive project documentation
    - Take on PM/PO role to build out development backlog
    - Create detailed issue descriptions for all team members

2. Associated Tasks
    - README Documentation Updates
    - Backlog Management and Issue Creation
    - Project Milestone Planning

3. Completed/In-Progress
    - Completed comprehensive README.md updates including:
        - Added Project Milestones section with clear goals for Milestone #1, #2, and #3
        - Added Getting Started section with current capabilities and installation instructions
        - Added API Reference section with core endpoints for Milestone #2
        - Improved project structure and documentation organization
    - Completed backlog creation as PM/PO:
        - Created 18 detailed issue descriptions with user stories, acceptance criteria, and technical requirements
        - Established clear dependencies between issues
        - Assigned story points and priorities for sprint planning
        - Created copy-paste ready issue descriptions for GitHub

### Reflection Points

**What went well:**
- Successfully took on the PM/PO role and created a comprehensive backlog that will guide the team's development efforts
- README updates should help users with getting started info and devs with planning.
- Issue descriptions provide clear direction for all team members, reducing ambiguity
- Established a structured approach to project management that will benefit future sprints

**What didn't go well:**
- Initially struggled with the scope of backlog creation - 18 issues was more extensive than anticipated
- Some issue descriptions required talking with a few members to make sure that the issue was on the right track
- Time management could have been better - spent more time on documentation than originally planned

### Planning Activities for Next Cycle

**Week 8 Goals:**
- Most likely will take on more of a dev role next week to start implementing features.
- Review and refine issue descriptions based on team feedback
- Begin sprint planning with team for Milestone #1 deliverables
- Focus on core infrastructure components that other features depend on

## Week 8
This section outlines the individual log for week 8

### October 20 - October 26

### Tasks
![](images/kaiden_week8_tasks.png)

### Weekly Goals

1. My Features: 
    - Implement text analyzer component for document analysis (R5: Media Metadata Extraction)
    - Create comprehensive test suite for text analyzer
    - Build CLI interface and example scripts for component usage

2. Associated Tasks
    - Text Analyzer Implementation
    - Test Suite Development
    - Documentation and Examples

3. Completed/In-Progress
    - Completed text analyzer core implementation:
        - Built `TextAnalyzer` class with support for PDF, DOCX, TXT, and MD files
        - Implemented 15+ metric extractions including word count, sentence count, paragraph count, reading time estimation, lexical diversity, and keyword frequency analysis
        - Added batch processing capability with aggregate statistics across multiple files
        - Created structured `TextMetrics` dataclass for clean dictionary output
    - Completed test suite:
        - Wrote 11 comprehensive tests covering all file types, batch analysis, error handling, and metric validation
        - All tests passing with pytest
        - Tests use temporary files with automatic cleanup
    - Completed supporting tools:
        - Built CLI wrapper (`analyze_text.py`) for command-line usage with pure JSON output
        - Created example script (`example_txt_analysis.py`) that generates sample files and demonstrates usage
        - Added robust import handling to work from any directory
    - Documentation:
        - Created comprehensive README for the text analyzer component
        - Wrote PR template with detailed description of changes
        - Documented usage examples for both CLI and Python API

## Week 9
This section outlines the individual log for week 9

### October 27 - November 2

### Tasks
![](images/kaiden_week9_tasks.png)

### Weekly Goals

1. My Features:
    - Fix PDF analysis bug in `TextAnalyzer` (initialize `heading_info` for PDF branch)
    - Research and draft the user-facing analysis report structure (brainstormed `REPORT_TEMPLATE.md`)
    - Plan how to connect standalone components into a pipeline (ingest → categorize → analyze)

2. Associated Tasks
    - Bugfix: PDF analyzer UnboundLocalError
    - Report template brainstorming/documentation
    - Pipeline architecture planning

3. Completed/In-Progress
    - Completed PDF bugfix by initializing `heading_info = None` in the PDF path to prevent `UnboundLocalError`
    - Created a markdown report template outlining sections for code, documents, images, videos, activity, insights, and metrics summary
    - Drafted an integration plan to route categorized files to the correct analyzers and aggregate results for API response

### Reflection Points

**What went well:**
- Identified and fixed the PDF-specific error quickly without impacting TXT/DOCX/MD paths
- The report template provides clarity on what the end-user will see and helps guide development
- Clearer vision for the end-to-end pipeline after planning

**What didn't go well:**
- Some churn around script/module import paths when running analyzer from different directories
- Time split across bugfix and documentation limited time for coding the orchestrator

### Planning Activities for Next Cycle

**Week 10 Goals:**
- Look into how we are going to faciliate the pipeline (maybe implement an orchestrator)
- Define endpoint for API call to trigger the pipeline  
- Optional: introduce a `PipelineConfig` to toggle categories (code/docs/media) and LLM usage


