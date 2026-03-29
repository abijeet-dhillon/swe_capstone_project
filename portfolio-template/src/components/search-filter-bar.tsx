"use client";

import React from "react";
import { motion } from "framer-motion";
import { Search, X } from "lucide-react";

interface SearchFilterBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  tags: string[];
  activeTag: string | null;
  onTagChange: (tag: string) => void;
}

export function SearchFilterBar({
  search,
  onSearchChange,
  tags,
  activeTag,
  onTagChange,
}: SearchFilterBarProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.4 }}
      className="sticky top-0 z-40 border-b border-zinc-800 bg-[#09090b]/90 px-6 py-4 backdrop-blur-md"
    >
      <div className="mx-auto flex max-w-6xl flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search projects, skills..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 py-2 pl-9 pr-8 text-sm text-zinc-200 placeholder-zinc-500 outline-none transition-colors focus:border-zinc-500"
          />
          {search && (
            <button
              onClick={() => onSearchChange("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5 overflow-x-auto">
          {tags.map((tag) => (
            <button
              key={tag}
              onClick={() => onTagChange(tag)}
              className={`whitespace-nowrap rounded-md px-2.5 py-1 font-mono text-xs transition-colors ${
                activeTag === tag
                  ? "bg-zinc-100 text-zinc-900"
                  : "border border-zinc-700/50 bg-zinc-800/80 text-zinc-400 hover:border-zinc-600 hover:text-zinc-200"
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
