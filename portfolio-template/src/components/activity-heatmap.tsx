"use client";
import React, { useMemo } from "react";
import { motion } from "framer-motion";
import { SectionHeading } from "./section-heading";
import type { HeatmapData } from "@/types/portfolio";

const DAYS = ["Mon", "", "Wed", "", "Fri", "", "Sun"];
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function cellColor(count: number, max: number) {
  if (!count || !max) return "bg-zinc-800";
  const r = count / max;
  if (r < 0.25) return "bg-emerald-900";
  if (r < 0.5)  return "bg-emerald-700";
  if (r < 0.75) return "bg-emerald-500";
  return "bg-emerald-400";
}

export function ActivityHeatmap({ heatmap }: { heatmap: HeatmapData }) {
  const { weeks, total_activity, date_range } = heatmap;
  const { columns, monthLabels, maxCount } = useMemo(() => {
    const sorted = Object.entries(weeks).sort(([a], [b]) => a.localeCompare(b));
    const max = Math.max(1, ...sorted.map(([, v]) => v));
    const cols = sorted.map(([weekKey, total]) => {
      const base = Math.floor(total / 7), rem = total % 7;
      return { weekKey, cells: Array.from({ length: 7 }, (_, i) => ({ day: i, count: base + (i < rem ? 1 : 0) })) };
    });
    const labels: { col: number; label: string }[] = [];
    let lastMonth = -1;
    cols.forEach(({ weekKey }, i) => {
      const m = new Date(weekKey).getMonth();
      if (m !== lastMonth) { labels.push({ col: i, label: MONTHS[m] }); lastMonth = m; }
    });
    return { columns: cols, monthLabels: labels, maxCount: max };
  }, [weeks]);

  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <SectionHeading title="Activity Heatmap" subtitle="Project commit activity over time" />
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-50px" }} transition={{ duration: 0.5 }} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
          <div className="mb-1 flex" style={{ marginLeft: 32 }}>
            {monthLabels.map(({ col, label }) => (
              <div key={`${col}-${label}`} className="text-xs text-zinc-500" style={{ position: "relative", left: col * 14, minWidth: 0 }}>{label}</div>
            ))}
          </div>
          <div className="flex gap-1">
            <div className="flex flex-col gap-[2px] mr-1">
              {DAYS.map((d, i) => <div key={i} className="h-[10px] text-[10px] leading-[10px] text-zinc-600 w-6 text-right">{d}</div>)}
            </div>
            <div className="flex gap-[2px] overflow-x-auto pb-1">
              {columns.map(({ weekKey, cells }) => (
                <div key={weekKey} className="flex flex-col gap-[2px]">
                  {cells.map(({ day, count }) => (
                    <div key={day} title={`${weekKey} +${day}d: ${count}`} className={`h-[10px] w-[10px] rounded-[2px] ${cellColor(count, maxCount)}`} />
                  ))}
                </div>
              ))}
            </div>
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-1 text-xs text-zinc-500">
              <span>Less</span>
              {["bg-zinc-800","bg-emerald-900","bg-emerald-700","bg-emerald-500","bg-emerald-400"].map((c) => (
                <div key={c} className={`h-[10px] w-[10px] rounded-[2px] ${c}`} />
              ))}
              <span>More</span>
            </div>
            <p className="text-xs text-zinc-500">{total_activity.toLocaleString()} commits · {date_range.start} → {date_range.end}</p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
