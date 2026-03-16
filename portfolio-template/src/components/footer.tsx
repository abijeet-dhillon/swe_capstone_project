import { Github, Linkedin, Twitter } from "lucide-react";
import type { DeveloperProfile } from "@/types/portfolio";

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  github: Github,
  linkedin: Linkedin,
  twitter: Twitter,
};

interface FooterProps {
  profile: DeveloperProfile;
}

export function Footer({ profile }: FooterProps) {
  return (
    <footer className="border-t border-zinc-800 px-6 py-10">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
        <p className="font-mono text-sm text-zinc-500">
          &copy; {new Date().getFullYear()} {profile.name}
        </p>
        <div className="flex items-center gap-4">
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
                className="text-zinc-600 transition-colors hover:text-zinc-400"
              >
                <Icon className="h-4 w-4" />
              </a>
            );
          })}
        </div>
      </div>
    </footer>
  );
}
