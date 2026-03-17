"use client";

import React from "react";
import { SectionHeading } from "./section-heading";
import { ProjectCard } from "./project-card";
import type { Project } from "@/types/portfolio";

interface ProjectsGridProps {
  projects: Project[];
}

export function ProjectsGrid({ projects }: ProjectsGridProps) {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <SectionHeading
          title="Projects"
          subtitle="A selection of things I have built"
        />

        <div className="grid gap-4 sm:grid-cols-2">
          {projects.map((project) => (
            <ProjectCard
              key={project.title}
              project={project}
              featured={project.featured}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
