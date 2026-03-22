import type { DeveloperProfile } from "@/types/portfolio";

export const portfolio: DeveloperProfile = {
  name: "Kaiden Merchant", title: "Software Engineer",
  bio: "Software Engineer focused on Python and React, building scalable full-stack applications.",
  avatarUrl: "/avatar-placeholder.jpg", resumeUrl: "/resume.pdf",
  email: "kaiden@gmail.com", location: "Kelowna, BC",
  socials: [
    { platform: "GitHub", url: "kaiden@github.com", icon: "github" },
    { platform: "LinkedIn", url: "kaiden@linkedin.com", icon: "linkedin" },
  ],
  about: {
    description: ["Software Engineer focused on Python and React, building scalable full-stack applications."],
    highlights: [{ label: "Years Experience", value: "2" }, { label: "Projects Completed", value: "100" }, { label: "Open Source Contributions", value: "1" }],
  },
  skills: [
    { name: "Languages", skills: ["java", "python"] },
    { name: "Tools & Skills", skills: ["numpy", "object-oriented-programming", "pandas"] },
    { name: "Frameworks", skills: ["numpy", "pandas"] },
  ],
  projects: [
    { title: "project1", description: "2 source files, 13 lines of code.", image: "/placeholder-project.jpg", tags: ["java", "python"], featured: true },
    { title: "ml-recommendation-engine", description: "1 source file, 211 lines of code.", image: "/placeholder-project.jpg", tags: ["python", "numpy", "pandas"], featured: true },
  ],
  experience: [],
  heatmap: {
    weeks: { "2025-01-06": 3, "2025-01-13": 7, "2025-01-20": 2, "2025-01-27": 5, "2025-02-03": 8, "2025-02-10": 4, "2025-02-17": 6, "2025-02-24": 9, "2025-03-03": 2, "2025-03-10": 5, "2025-03-17": 11, "2025-03-24": 3, "2025-04-07": 6, "2025-04-14": 8, "2025-04-21": 4, "2025-04-28": 7 },
    total_weeks: 16, total_activity: 90, date_range: { start: "2025-01-06", end: "2025-04-28" },
  },
  showcase: [
    { rank: 1, project_id: 1, project_title: "ml-recommendation-engine", score: 142.5, summary: "ML recommendation system built with Python, pandas, and scikit-learn.", key_skills: ["python", "pandas", "scikit-learn", "numpy"], key_metrics: { total_files: 18, total_lines: 2100, total_commits: 45, total_contributors: 2, doc_files: 3, image_files: 0, video_files: 0, test_files: 5 }, evolution: { first_commit_at: "2025-01-10", last_commit_at: "2025-04-20", duration_days: 100, total_commits: 45, contributors: ["Alice", "Bob"], activity_mix: { code: 0.7, docs: 0.2, tests: 0.1 } } },
    { rank: 2, project_id: 2, project_title: "project1", score: 88.0, summary: "Full-stack web project with React and FastAPI.", key_skills: ["react", "fastapi", "python", "typescript"], key_metrics: { total_files: 10, total_lines: 900, total_commits: 22, total_contributors: 3, doc_files: 1, image_files: 2, video_files: 0, test_files: 3 }, evolution: { first_commit_at: "2025-02-01", last_commit_at: "2025-04-15", duration_days: 73, total_commits: 22, contributors: ["Alice", "Bob", "Carol"], activity_mix: { code: 0.8, docs: 0.1, tests: 0.1 } } },
  ],
};
