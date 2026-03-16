import { portfolio } from "@/config/portfolio";
import { Hero } from "@/components/hero";
import { Footer } from "@/components/footer";

export default function Home() {
  return (
    <main className="min-h-screen">
      <Hero profile={portfolio} />

      {/* Future sections: About, Skills, Projects, Experience, Contact */}

      <Footer profile={portfolio} />
    </main>
  );
}
