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
  total_activity: number;
  date_range: { start: string; end: string };
}

export interface ShowcaseProject {
  project_id: number;
  rank: number;
  project_title: string;
  score: number;
  summary?: string;
  key_skills: string[];
  key_metrics: { total_contributors: number };
  evolution: {
    total_commits: number;
    duration_days: number;
    contributors: string[];
    first_commit_at?: string;
    last_commit_at?: string;
  };
}

export interface PortfolioCustomization {
  hiddenSections: string[];
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
  heatmap?: HeatmapData;
  showcase?: ShowcaseProject[];
  hiddenSections?: string[];
}
