"use client";
import React from "react";
import { motion } from "framer-motion";
import { SectionHeading } from "./section-heading";
import type { ShowcaseProject } from "@/types/portfolio";

const MEDAL = ["🥇", "🥈", "🥉"];

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className="text-lg font-bold text-zinc-100">{value}</span>
      <span className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</span>
    </div>
  );
}

export function TopShowcase({ projects }: { projects: ShowcaseProject[] }) {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <SectionHeading title="Top Projects" subtitle="Highest-impact work ranked by contributions" />
        <div className="grid gap-6 sm:grid-cols-3">
          {projects.map((p, i) => (
            <motion.article key={p.project_id} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-40px" }} transition={{ duration: 0.4, delay: i * 0.1 }} className="flex flex-col rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 hover:border-zinc-700 transition-colors">
              <div className="mb-4 flex items-start gap-3">
                <span className="text-2xl leading-none">{MEDAL[i] ?? `#${p.rank}`}</span>
                <div>
                  <h3 className="font-semibold text-zinc-100 leading-snug">{p.project_title}</h3>
                  <p className="text-xs text-zinc-500 mt-0.5">score {p.score.toFixed(1)}</p>
                </div>
              </div>
              {p.summary && <p className="mb-4 text-sm leading-relaxed text-zinc-400 flex-1">{p.summary}</p>}
              <div className="mb-4 grid grid-cols-3 gap-2 rounded-lg bg-zinc-800/50 px-3 py-3">
                <Stat label="commits" value={p.evolution.total_commits} />
                <Stat label="days" value={p.evolution.duration_days} />
                <Stat label="contributors" value={p.evolution.contributors.length || p.key_metrics.total_contributors} />
              </div>
              {p.evolution.first_commit_at && (
                <p className="mb-4 text-[11px] text-zinc-600">{p.evolution.first_commit_at.slice(0, 10)} → {(p.evolution.last_commit_at ?? "").slice(0, 10)}</p>
              )}
              <div className="flex flex-wrap gap-1.5">
                {p.key_skills.slice(0, 6).map((s) => (
                  <span key={s} className="rounded-md bg-zinc-800 px-2 py-0.5 font-mono text-xs text-zinc-400">{s}</span>
                ))}
              </div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
