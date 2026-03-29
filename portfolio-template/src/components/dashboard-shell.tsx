"use client";

import React, { useState, useMemo } from "react";
import { Hero } from "./hero";
import { About } from "./about";
import { Skills } from "./skills";
import { ActivityHeatmap } from "./activity-heatmap";
import { TopShowcase } from "./top-showcase";
import { ProjectsGrid } from "./projects-grid";
import { Footer } from "./footer";
import { SearchFilterBar } from "./search-filter-bar";
import type { DeveloperProfile } from "@/types/portfolio";

type SectionId = "about" | "skills" | "heatmap" | "showcase" | "projects";

export function DashboardShell({ profile }: { profile: DeveloperProfile }) {
  const [search, setSearch] = useState("");
  const [activeTag, setActiveTag] = useState<string | null>(null);

  const hidden = useMemo<Set<SectionId>>(() => {
    return new Set((profile.hiddenSections ?? []) as SectionId[]);
  }, [profile.hiddenSections]);

  const allTags = useMemo(() => {
    const set = new Set<string>();
    profile.projects.forEach((p) => p.tags.forEach((t) => set.add(t)));
    return [...set].sort();
  }, [profile.projects]);

  const filteredProjects = useMemo(() => {
    const q = search.toLowerCase().trim();
    return profile.projects.filter((p) => {
      if (activeTag && !p.tags.includes(activeTag)) return false;
      if (!q) return true;
      return (
        p.title.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.tags.some((t) => t.toLowerCase().includes(q))
      );
    });
  }, [profile.projects, search, activeTag]);

  const filteredSkills = useMemo(() => {
    const q = search.toLowerCase().trim();
    if (!q && !activeTag) return profile.skills;
    return profile.skills
      .map((cat) => ({
        ...cat,
        skills: cat.skills.filter((s) => {
          if (activeTag && s.toLowerCase() !== activeTag.toLowerCase()) return false;
          if (q && !s.toLowerCase().includes(q)) return false;
          return true;
        }),
      }))
      .filter((cat) => cat.skills.length > 0);
  }, [profile.skills, search, activeTag]);

  const filteredShowcase = useMemo(() => {
    if (!profile.showcase) return [];
    const q = search.toLowerCase().trim();
    return profile.showcase.filter((p) => {
      if (activeTag && !p.key_skills.map((s) => s.toLowerCase()).includes(activeTag.toLowerCase()))
        return false;
      if (!q) return true;
      return (
        p.project_title.toLowerCase().includes(q) ||
        p.key_skills.some((s) => s.toLowerCase().includes(q))
      );
    });
  }, [profile.showcase, search, activeTag]);

  const visible = (id: SectionId) => !hidden.has(id);

  return (
    <main className="min-h-screen">
      <Hero profile={profile} />

      <SearchFilterBar
        search={search}
        onSearchChange={setSearch}
        tags={allTags}
        activeTag={activeTag}
        onTagChange={(t) => setActiveTag(t === activeTag ? null : t)}
      />

      {visible("about") && <About profile={profile} />}
      {visible("skills") && filteredSkills.length > 0 && <Skills skills={filteredSkills} />}
      {visible("heatmap") && profile.heatmap && <ActivityHeatmap heatmap={profile.heatmap} />}
      {visible("showcase") && filteredShowcase.length > 0 && (
        <TopShowcase projects={filteredShowcase} />
      )}
      {visible("projects") && <ProjectsGrid projects={filteredProjects} />}

      <Footer profile={profile} />
    </main>
  );
}
