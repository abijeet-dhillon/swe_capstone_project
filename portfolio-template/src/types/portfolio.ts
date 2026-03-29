export interface SocialLink {
  platform: string;
  url: string;
  icon: string;
}

export interface Project {
  title: string;
  description: string;
  image: string;
  tags: string[];
  liveUrl?: string;
  sourceUrl?: string;
  featured?: boolean;
}

export interface Experience {
  company: string;
  role: string;
  startDate: string;
  endDate: string;
  description: string[];
  logo?: string;
}

export interface SkillCategory {
  name: string;
  skills: string[];
}

export interface HeatmapData {
  weeks: Record<string, number>;
  total_weeks: number;
  total_activity: number;
  date_range: { start: string; end: string };
}

export interface ShowcaseProject {
  rank: number;
  project_id: number;
  project_title: string;
  score: number;
  summary: string;
  key_skills: string[];
  key_metrics: {
    total_files: number;
    total_lines: number;
    total_commits: number;
    total_contributors: number;
    doc_files: number;
    image_files: number;
    video_files: number;
    test_files: number;
  };
  evolution: {
    first_commit_at: string | null;
    last_commit_at: string | null;
    duration_days: number;
    total_commits: number;
    contributors: string[];
    activity_mix: Record<string, number>;
  };
}

/** A single skill with its progression metadata derived from the timeline. */
export interface SkillProgressionItem {
  skill: string;
  category: string;
  /** ISO date string of first recorded appearance, e.g. "2023-03" */
  firstSeen: string;
  /** ISO date string of most recent appearance, e.g. "2024-11" */
  lastSeen: string;
  /** Fractional years from firstSeen to lastSeen (clamped to ≥ 0) */
  yearsExperience: number;
  /** Number of distinct projects where this skill appears */
  projectCount: number;
}

/** One time-bucket (e.g. a year) containing the skills that first appeared then. */
export interface SkillTimelineEntry {
  period: string;        // "2022", "2023", …
  year: number;
  newSkills: SkillProgressionItem[];
}

export interface DeveloperProfile {
  name: string;
  title: string;
  bio: string;
  avatarUrl: string;
  resumeUrl: string;
  email: string;
  location: string;
  socials: SocialLink[];
  about: {
    description: string[];
    highlights: { label: string; value: string }[];
  };
  skills: SkillCategory[];
  projects: Project[];
  experience: Experience[];
  /** Optional: heatmap of weekly activity */
  heatmap?: HeatmapData;
  /** Optional: top showcase projects */
  showcase?: ShowcaseProject[];
  /** Optional: chronological skill progression for the portfolio timeline section */
  skillsTimeline?: SkillTimelineEntry[];
  hiddenSections?: string[];
}
