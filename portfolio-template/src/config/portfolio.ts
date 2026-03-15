import type { DeveloperProfile } from "@/types/portfolio";

export const portfolio: DeveloperProfile = {
  name: "Alex Chen",
  title: "Full-Stack Developer",
  bio: "I build polished, accessible web experiences with modern tools. Currently focused on design systems and developer tooling.",
  avatarUrl: "/avatar-placeholder.jpg",
  resumeUrl: "/resume.pdf",
  email: "alex@example.com",
  location: "Vancouver, BC",

  socials: [
    { platform: "GitHub", url: "https://github.com", icon: "github" },
    { platform: "LinkedIn", url: "https://linkedin.com", icon: "linkedin" },
    { platform: "Twitter", url: "https://twitter.com", icon: "twitter" },
  ],

  about: {
    description: [
      "I'm a full-stack developer with a passion for building clean, performant web applications. With experience across the entire stack, I enjoy turning complex problems into simple, elegant solutions.",
      "When I'm not coding, you can find me contributing to open-source projects, writing technical blog posts, or exploring the outdoors.",
    ],
    highlights: [
      { label: "Years Experience", value: "4+" },
      { label: "Projects Completed", value: "20+" },
      { label: "Open Source Contributions", value: "50+" },
    ],
  },

  skills: [
    {
      name: "Languages",
      skills: ["TypeScript", "Python", "JavaScript", "Go", "SQL"],
    },
    {
      name: "Frontend",
      skills: ["React", "Next.js", "Tailwind CSS", "Framer Motion"],
    },
    {
      name: "Backend",
      skills: ["Node.js", "FastAPI", "PostgreSQL", "Redis"],
    },
    {
      name: "Tools",
      skills: ["Git", "Docker", "Figma", "Vercel", "AWS"],
    },
  ],

  projects: [
    {
      title: "DevBoard",
      description:
        "A real-time project management dashboard built for developer teams. Features Kanban boards, sprint tracking, and GitHub integration.",
      image: "/placeholder-project.jpg",
      tags: ["Next.js", "TypeScript", "Prisma", "WebSockets"],
      liveUrl: "https://example.com",
      sourceUrl: "https://github.com",
      featured: true,
    },
    {
      title: "Synthwave UI",
      description:
        "An open-source component library with a retro-futuristic aesthetic. Fully accessible and tree-shakeable.",
      image: "/placeholder-project.jpg",
      tags: ["React", "Storybook", "Radix UI", "CSS"],
      sourceUrl: "https://github.com",
      featured: true,
    },
    {
      title: "CloudCast",
      description:
        "A weather application with hyper-local forecasts, interactive radar maps, and severe weather alerts.",
      image: "/placeholder-project.jpg",
      tags: ["React Native", "GraphQL", "Mapbox"],
      liveUrl: "https://example.com",
    },
    {
      title: "Terracotta",
      description:
        "A CLI tool for scaffolding full-stack applications with pre-configured auth, database, and deployment pipelines.",
      image: "/placeholder-project.jpg",
      tags: ["Go", "Cobra", "Docker", "PostgreSQL"],
      sourceUrl: "https://github.com",
    },
  ],

  experience: [
    {
      company: "Nexus Technologies",
      role: "Software Engineer",
      startDate: "Jan 2024",
      endDate: "Present",
      description: [
        "Led the rebuild of the customer-facing dashboard, improving load times by 40%.",
        "Designed and shipped a component library adopted by 3 product teams.",
        "Mentored 2 junior developers through onboarding and code reviews.",
      ],
    },
    {
      company: "Bright Studio",
      role: "Frontend Developer",
      startDate: "Jun 2022",
      endDate: "Dec 2023",
      description: [
        "Built responsive marketing pages and product landing sites for clients.",
        "Integrated headless CMS solutions reducing content update turnaround by 60%.",
        "Implemented analytics tracking and A/B testing infrastructure.",
      ],
    },
    {
      company: "Open Source",
      role: "Contributor",
      startDate: "2021",
      endDate: "Present",
      description: [
        "Active contributor to several popular React and TypeScript libraries.",
        "Authored and maintained a CSS utility library with 500+ GitHub stars.",
      ],
    },
  ],
};
