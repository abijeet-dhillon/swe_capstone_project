import type { DeveloperProfile } from "@/types/portfolio";

export const portfolio: DeveloperProfile = {
  name: "Sam Sikora",
  title: "Full-Stack Developer",
  bio: "I am a developer",
  avatarUrl: "/avatar-placeholder.jpg",
  resumeUrl: "/resume.pdf",
  email: "",
  location: "",

  socials: [
    
  ],

  about: {
    description: [
      "I am a developer"
    ],
    highlights: [
      { label: "Projects Completed", value: "49" }
    ],
  },

  skills: [
    {
      name: "Languages",
      skills: ["carbon", "gdscript", "javascript", "text only", "transact-sql"],
    },
    {
      name: "Frameworks",
      skills: ["jest", "node"],
    },
    {
      name: "Tools & Skills",
      skills: ["arrow-functions", "carbon", "gdscript", "javascript", "jest", "node", "react-hooks", "text only", "transact-sql"],
    }
  ],

  projects: [
    {
      title: "A3-MishaGavura-48541528",
      description: "A comprehensive project comprising 5 source files and 1,704 lines of code.",
      image: "/placeholder-project.jpg",
      tags: ["javascript", "jest"],
      featured: true,
    },
    {
      title: "SuperBugZapper",
      description: "A comprehensive project comprising 1 source file and 201 lines of code.",
      image: "/placeholder-project.jpg",
      tags: ["javascript"],
      featured: true,
    },
    {
      title: "monapure-upsell",
      description: "A comprehensive project comprising 11 source files and 528 lines of code. The project features extensive documentation.",
      image: "/placeholder-project.jpg",
      tags: ["carbon", "gdscript", "javascript", "jest", "node", "arrow-functions"],
    }
  ],

  experience: [],
};
