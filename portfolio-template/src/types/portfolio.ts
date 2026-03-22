export interface SocialLink { platform: string; url: string; icon: string }
export interface Project { title: string; description: string; image: string; tags: string[]; liveUrl?: string; sourceUrl?: string; featured?: boolean }
export interface Experience { company: string; role: string; startDate: string; endDate: string; description: string[]; logo?: string }
export interface SkillCategory { name: string; skills: string[] }
export interface HeatmapData {
  weeks: Record<string, number>;
  total_weeks: number;
  total_activity: number;
  date_range: { start: string; end: string };
}
export interface ShowcaseProject {
  rank: number; project_id: number; project_title: string; score: number; summary?: string; key_skills: string[];
  key_metrics: { total_files: number; total_lines: number; total_commits: number; total_contributors: number; doc_files: number; image_files: number; video_files: number; test_files: number };
  evolution: { first_commit_at?: string; last_commit_at?: string; duration_days: number; total_commits: number; contributors: string[]; activity_mix: Record<string, number> };
}
export interface DeveloperProfile {
  name: string; title: string; bio: string; avatarUrl: string; resumeUrl: string; email: string; location: string;
  socials: SocialLink[];
  about: { description: string[]; highlights: { label: string; value: string }[] };
  skills: SkillCategory[];
  projects: Project[];
  experience: Experience[];
  heatmap?: HeatmapData;
  showcase?: ShowcaseProject[];
}
