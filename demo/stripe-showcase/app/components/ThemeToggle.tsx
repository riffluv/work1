"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    // 初回: localStorageから復元（なければlight）
    const saved = localStorage.getItem("theme") as Theme | null;
    const initial = saved === "dark" ? "dark" : "light";
    setTheme(initial);
    document.documentElement.setAttribute("data-theme", initial);
  }, []);

  const toggle = () => {
    const next: Theme = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  };

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggle}
      aria-label={`${theme === "light" ? "ダーク" : "ライト"}モードに切り替え`}
    >
      <span className="theme-toggle-icon">
        {theme === "light" ? "☀️" : "🌙"}
      </span>
      {theme === "light" ? "Light" : "Dark"}
    </button>
  );
}
