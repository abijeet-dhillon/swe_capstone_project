import { portfolio } from "@/config/portfolio";
import { Hero } from "@/components/hero";
import { About } from "@/components/about";
import { Skills } from "@/components/skills";
import { ProjectsGrid } from "@/components/projects-grid";
import { Footer } from "@/components/footer";

export default function Home() {
  return (
    <main className="min-h-screen">
      <Hero profile={portfolio} />
      <About profile={portfolio} />
      <Skills skills={portfolio.skills} />
      <ProjectsGrid projects={portfolio.projects} />

      {/* Future sections: Experience, Contact */}

      <Footer profile={portfolio} />
    </main>
  );
}
