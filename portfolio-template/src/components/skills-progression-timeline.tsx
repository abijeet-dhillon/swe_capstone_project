"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SectionHeading } from "./section-heading";
import type { SkillTimelineEntry, SkillProgressionItem } from "@/types/portfolio";

interface SkillsProgressionTimelineProps {
  timeline: SkillTimelineEntry[];
}

const CATEGORY_COLORS: Record<string, string> = {
  language:   "bg-blue-900/60 text-blue-300 border-blue-700/50",
  languages:  "bg-blue-900/60 text-blue-300 border-blue-700/50",
  framework:  "bg-purple-900/60 text-purple-300 border-purple-700/50",
  frameworks: "bg-purple-900/60 text-purple-300 border-purple-700/50",
  tool:       "bg-amber-900/60 text-amber-300 border-amber-700/50",
  tools:      "bg-amber-900/60 text-amber-300 border-amber-700/50",
  general:    "bg-zinc-800/60 text-zinc-300 border-zinc-700/50",
  manual:     "bg-zinc-800/60 text-zinc-300 border-zinc-700/50",
};

function categoryColor(category: string): string {
  const key = category.toLowerCase().replace(/\s+/g, "");
  for (const [prefix, cls] of Object.entries(CATEGORY_COLORS)) {
    if (key.startsWith(prefix)) return cls;
  }
  return CATEGORY_COLORS.general;
}

/** Render a thin horizontal bar representing years of experience (capped at 10 yrs). */
function ExperienceBar({ years }: { years: number }) {
  const MAX = 10;
  const pct = Math.min(100, Math.round((years / MAX) * 100));
  return (
    <div className="mt-1.5 flex items-center gap-2">
      <div className="h-1.5 flex-1 rounded-full bg-zinc-700/60">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400"
          initial={{ width: 0 }}
          whileInView={{ width: `${pct}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
      <span className="shrink-0 font-mono text-xs text-zinc-400">
        {years < 1 ? "<1 yr" : `${years} yr${years === 1 ? "" : "s"}`}
      </span>
    </div>
  );
}

function SkillCard({ skill }: { skill: SkillProgressionItem }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-30px" }}
      transition={{ duration: 0.35 }}
      className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 hover:border-zinc-700 transition-colors"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="font-medium text-zinc-100 text-sm leading-snug">{skill.skill}</span>
        <span
          className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-mono uppercase tracking-wide ${categoryColor(skill.category)}`}
        >
          {skill.category}
        </span>
      </div>
      <ExperienceBar years={skill.yearsExperience} />
      {skill.projectCount > 1 && (
        <p className="mt-1 text-[11px] text-zinc-500">
          Used in {skill.projectCount} project{skill.projectCount > 1 ? "s" : ""}
        </p>
      )}
    </motion.div>
  );
}

function YearBucket({ entry, isLast }: { entry: SkillTimelineEntry; isLast: boolean }) {
  const [expanded, setExpanded] = useState(true);
  const MAX_PREVIEW = 6;
  const showAll = entry.newSkills.length <= MAX_PREVIEW;

  return (
    <div className="relative flex gap-6">
      {/* Vertical line */}
      <div className="flex flex-col items-center">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 border-indigo-500 bg-zinc-900 z-10">
          <span className="font-mono text-xs font-bold text-indigo-400">{entry.year}</span>
        </div>
        {!isLast && (
          <div className="mt-1 w-px flex-1 bg-gradient-to-b from-indigo-500/50 to-zinc-700/30" />
        )}
      </div>

      {/* Content */}
      <div className="mb-10 flex-1 pt-1.5">
        <button
          onClick={() => setExpanded((p) => !p)}
          className="mb-3 flex items-center gap-2 text-left"
        >
          <h3 className="text-lg font-semibold text-zinc-200">
            {entry.period}
          </h3>
          <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400">
            {entry.newSkills.length} new skill{entry.newSkills.length !== 1 ? "s" : ""}
          </span>
          <span className="ml-auto text-zinc-500 text-xs select-none">
            {expanded ? "▲ collapse" : "▼ expand"}
          </span>
        </button>

        <AnimatePresence initial={false}>
          {expanded && (
            <motion.div
              key="content"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <CollapsibleSkillGrid skills={entry.newSkills} maxPreview={MAX_PREVIEW} showAll={showAll} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function CollapsibleSkillGrid({
  skills,
  maxPreview,
  showAll: initialShowAll,
}: {
  skills: SkillProgressionItem[];
  maxPreview: number;
  showAll: boolean;
}) {
  const [showAll, setShowAll] = useState(initialShowAll);
  const visible = showAll ? skills : skills.slice(0, maxPreview);

  return (
    <div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {visible.map((sk) => (
          <SkillCard key={sk.skill} skill={sk} />
        ))}
      </div>
      {!initialShowAll && (
        <button
          onClick={() => setShowAll((p) => !p)}
          className="mt-3 text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          {showAll ? `Show less` : `Show ${skills.length - maxPreview} more…`}
        </button>
      )}
    </div>
  );
}

export function SkillsProgressionTimeline({ timeline }: SkillsProgressionTimelineProps) {
  if (!timeline || timeline.length === 0) return null;

  const totalSkills = timeline.reduce((sum, b) => sum + b.newSkills.length, 0);

  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-4xl">
        <SectionHeading
          title="Skills Progression"
          subtitle={`${totalSkills} skill${totalSkills !== 1 ? "s" : ""} tracked across ${timeline.length} year${timeline.length !== 1 ? "s" : ""} of learning`}
        />

        <div className="mt-8">
          {timeline.map((entry, i) => (
            <YearBucket
              key={entry.year}
              entry={entry}
              isLast={i === timeline.length - 1}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
