"use client";

import React, { useMemo } from "react";
import { Hero } from "./hero";
import { About } from "./about";
import { Skills } from "./skills";
import { ActivityHeatmap } from "./activity-heatmap";
import { SkillsProgressionTimeline } from "./skills-progression-timeline";
import { TopShowcase } from "./top-showcase";
import { ProjectsGrid } from "./projects-grid";
import { Footer } from "./footer";
import type { DeveloperProfile } from "@/types/portfolio";

type SectionId = "about" | "skills" | "skillsTimeline" | "heatmap" | "showcase" | "projects";

export function DashboardShell({ profile }: { profile: DeveloperProfile }) {
  const hidden = useMemo<Set<SectionId>>(() => {
    return new Set((profile.hiddenSections ?? []) as SectionId[]);
  }, [profile.hiddenSections]);

  const showcase = profile.showcase ?? [];

  const visible = (id: SectionId) => !hidden.has(id);

  return (
    <main className="min-h-screen">
      <Hero profile={profile} />

      {visible("about") && <About profile={profile} />}
      {visible("skills") && profile.skills.length > 0 && <Skills skills={profile.skills} />}
      {visible("skillsTimeline") && profile.skillsTimeline && profile.skillsTimeline.length > 0 && (
        <SkillsProgressionTimeline timeline={profile.skillsTimeline} />
      )}
      {visible("heatmap") && profile.heatmap && <ActivityHeatmap heatmap={profile.heatmap} />}
      {visible("showcase") && showcase.length > 0 && (
        <TopShowcase projects={showcase} />
      )}
      {visible("projects") && <ProjectsGrid projects={profile.projects} />}

      <Footer profile={profile} />
    </main>
  );
}
