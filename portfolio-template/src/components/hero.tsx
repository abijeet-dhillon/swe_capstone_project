"use client";

import { motion } from "framer-motion";
import { Github, Linkedin, Twitter, Mail, FileText } from "lucide-react";
import type { DeveloperProfile } from "@/types/portfolio";

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  github: Github,
  linkedin: Linkedin,
  twitter: Twitter,
};

interface HeroProps {
  profile: DeveloperProfile;
}

export function Hero({ profile }: HeroProps) {
  return (
    <section className="flex min-h-[85vh] items-center justify-center px-6">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="mx-auto max-w-3xl text-center"
      >
        <p className="mb-4 font-mono text-sm tracking-wider text-zinc-500">
          {profile.location}
        </p>
        <h1 className="text-5xl font-bold tracking-tight text-zinc-100 sm:text-7xl">
          {profile.name}
        </h1>
        <p className="mt-2 text-xl font-medium text-zinc-400 sm:text-2xl">
          {profile.title}
        </p>
        <p className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-zinc-400">
          {profile.bio}
        </p>

        <div className="mt-8 flex items-center justify-center gap-4">
          <a
            href={profile.resumeUrl}
            className="inline-flex items-center gap-2 rounded-lg bg-zinc-100 px-5 py-2.5 text-sm font-medium text-zinc-900 transition-colors hover:bg-zinc-200"
          >
            <FileText className="h-4 w-4" />
            Resume
          </a>
          <a
            href={`mailto:${profile.email}`}
            className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 px-5 py-2.5 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-500 hover:text-zinc-100"
          >
            <Mail className="h-4 w-4" />
            Contact
          </a>
        </div>

        <div className="mt-8 flex items-center justify-center gap-5">
          {profile.socials.map((social) => {
            const Icon = iconMap[social.icon];
            if (!Icon) return null;
            return (
              <a
                key={social.platform}
                href={social.url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={social.platform}
                className="text-zinc-500 transition-colors hover:text-zinc-300"
              >
                <Icon className="h-5 w-5" />
              </a>
            );
          })}
        </div>
      </motion.div>
    </section>
  );
}
