import type { DeveloperProfile } from "@/types/portfolio";

export const portfolio: DeveloperProfile = {
  name: "Kaiden Merchant",
  title: "Software Engineer",
  bio: "I am a Software Engineer dedicated to building scalable, user-centric applications that solve real-world problems. With a core focus on Python and React, I enjoy bridging the gap between complex backend logic and seamless frontend experiences. I thrive in collaborative environments where clean code, architectural integrity, and efficient performance are the standard.",
  avatarUrl: "/avatar-placeholder.jpg",
  resumeUrl: "/resume.pdf",
  email: "kaiden@gmail.com",
  location: "Kelowna, BC",

  socials: [
    { platform: "GitHub", url: "kaiden@github.com", icon: "github" },
    { platform: "LinkedIn", url: "kaiden@linkedin.com", icon: "linkedin" }
  ],

  about: {
    description: [
      "I am a Software Engineer dedicated to building scalable, user-centric applications that solve real-world problems. With a core focus on Python and React, I enjoy bridging the gap between complex backend logic and seamless frontend experiences. I thrive in collaborative environments where clean code, architectural integrity, and efficient performance are the standard."
    ],
    highlights: [
      { label: "Years Experience", value: "2" },
      { label: "Projects Completed", value: "100" },
      { label: "Open Source Contributions", value: "1" }
    ],
  },

  skills: [
    {
      name: "Languages",
      skills: ["java", "python"],
    },
    {
      name: "Tools & Skills",
      skills: ["java", "numpy", "object-oriented-programming", "pandas", "python"],
    },
    {
      name: "Frameworks",
      skills: ["numpy", "pandas"],
    }
  ],

  projects: [
    {
      title: "project1",
      description: "A comprehensive project comprising 2 source files and 13 lines of code.",
      image: "/placeholder-project.jpg",
      tags: ["java", "python"],
      featured: true,
    },
    {
      title: "ml-recommendation-engine",
      description: "A comprehensive project comprising 1 source file and 211 lines of code.",
      image: "/placeholder-project.jpg",
      tags: ["python", "numpy", "pandas", "object-oriented-programming"],
      featured: true,
    }
  ],

  experience: [],
};
