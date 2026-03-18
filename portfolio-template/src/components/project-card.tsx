"use client";

import React from "react";
import { motion } from "framer-motion";
import { ExternalLink, Github } from "lucide-react";
import type { Project } from "@/types/portfolio";

interface ProjectCardProps {
  project: Project;
  featured?: boolean;
}

export function ProjectCard({ project, featured }: ProjectCardProps) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.4 }}
      className={`group relative flex flex-col overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/50 transition-colors hover:border-zinc-700 ${
        featured ? "sm:col-span-2 sm:flex-row" : ""
      }`}
    >
      <div
        className={`relative overflow-hidden bg-zinc-800 ${
          featured
            ? "aspect-16/10 sm:aspect-auto sm:w-1/2"
            : "aspect-16/10"
        }`}
      >
        <div className="flex h-full items-center justify-center text-zinc-600">
          <svg
            className="h-12 w-12"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1}
          >
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <path d="M21 15l-5-5L5 21" />
          </svg>
        </div>
      </div>

      <div className={`flex flex-1 flex-col p-5 ${featured ? "sm:p-6" : ""}`}>
        <div className="mb-3 flex items-start justify-between gap-3">
          <h3 className="text-lg font-semibold text-zinc-100">
            {project.title}
          </h3>
          <div className="flex shrink-0 gap-2">
            {project.sourceUrl && (
              <a
                href={project.sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`${project.title} source code`}
                className="text-zinc-500 transition-colors hover:text-zinc-300"
              >
                <Github className="h-4 w-4" />
              </a>
            )}
            {project.liveUrl && (
              <a
                href={project.liveUrl}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`${project.title} live demo`}
                className="text-zinc-500 transition-colors hover:text-zinc-300"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            )}
          </div>
        </div>

        <p className="mb-4 flex-1 text-sm leading-relaxed text-zinc-400">
          {project.description}
        </p>

        <div className="flex flex-wrap gap-1.5">
          {project.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-md bg-zinc-800 px-2 py-0.5 font-mono text-xs text-zinc-400"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </motion.article>
  );
}
