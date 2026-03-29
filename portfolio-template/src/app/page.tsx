import { portfolio } from "@/config/portfolio";
import { DashboardShell } from "@/components/dashboard-shell";

export default function Home() {
  return <DashboardShell profile={portfolio} />;
}
