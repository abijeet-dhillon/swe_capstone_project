import { portfolio } from "@/config/portfolio";
import { Hero } from "@/components/hero";
import { About } from "@/components/about";
import { Skills } from "@/components/skills";
import { ProjectsGrid } from "@/components/projects-grid";
import { ActivityHeatmap } from "@/components/activity-heatmap";
import { TopShowcase } from "@/components/top-showcase";
import { Footer } from "@/components/footer";

export default function Home() {
  return (
    <main className="min-h-screen">
      <Hero profile={portfolio} />
      <About profile={portfolio} />
      <Skills skills={portfolio.skills} />
      {portfolio.heatmap && <ActivityHeatmap heatmap={portfolio.heatmap} />}
      {portfolio.showcase && portfolio.showcase.length > 0 && (
        <TopShowcase projects={portfolio.showcase} />
      )}
      <ProjectsGrid projects={portfolio.projects} />
      <Footer profile={portfolio} />
    </main>
  );
}
