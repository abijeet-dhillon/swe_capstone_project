"use client";

import React from "react";
import { motion } from "framer-motion";
import { SectionHeading } from "./section-heading";
import type { SkillCategory } from "@/types/portfolio";

interface SkillsProps {
  skills: SkillCategory[];
}

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.08 },
  },
};

const tagVariants = {
  hidden: { opacity: 0, scale: 0.85 },
  visible: { opacity: 1, scale: 1 },
};

export function Skills({ skills }: SkillsProps) {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <SectionHeading
          title="Skills"
          subtitle="Technologies and tools I work with"
        />

        <div className="grid gap-8 sm:grid-cols-2">
          {skills.map((category) => (
            <motion.div
              key={category.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.4 }}
              className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6"
            >
              <h3 className="mb-4 font-mono text-sm font-medium tracking-wider text-zinc-400 uppercase">
                {category.name}
              </h3>
              <motion.div
                className="flex flex-wrap gap-2"
                variants={containerVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
              >
                {category.skills.map((skill) => (
                  <motion.span
                    key={skill}
                    variants={tagVariants}
                    className="rounded-md border border-zinc-700/50 bg-zinc-800/80 px-3 py-1.5 text-sm text-zinc-300 transition-colors hover:border-zinc-600 hover:text-zinc-100"
                  >
                    {skill}
                  </motion.span>
                ))}
              </motion.div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
