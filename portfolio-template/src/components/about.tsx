"use client";

import React from "react";
import { motion } from "framer-motion";
import { SectionHeading } from "./section-heading";
import type { DeveloperProfile } from "@/types/portfolio";

interface AboutProps {
  profile: DeveloperProfile;
}

export function About({ profile }: AboutProps) {
  const { about } = profile;

  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <SectionHeading title="About Me" subtitle="A bit more about who I am" />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="grid gap-12 md:grid-cols-5"
        >
          <div className="space-y-4 md:col-span-3">
            {about.description.map((paragraph, i) => (
              <p
                key={i}
                className="text-base leading-relaxed text-zinc-400"
              >
                {paragraph}
              </p>
            ))}
          </div>

          <div className="flex flex-col gap-4 md:col-span-2">
            {about.highlights.map((highlight, i) => (
              <div
                key={i}
                className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 text-center"
              >
                <p className="text-3xl font-bold text-zinc-100">
                  {highlight.value}
                </p>
                <p className="mt-1 font-mono text-xs tracking-wider text-zinc-500 uppercase">
                  {highlight.label}
                </p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
