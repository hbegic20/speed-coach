import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LanguageSwitcher } from "./language-switcher";

vi.mock("next/navigation", () => ({
  usePathname: () => "/en/audits/6f1c2a8e-3b4d-4c5e-9f60-7a8b9c0d1e2f",
}));

describe("LanguageSwitcher", () => {
  it("keeps the current page when switching language and marks the active one", () => {
    render(
      <LanguageSwitcher
        currentLocale="en"
        label="Language"
        languageNames={{ bs: "Bosanski", en: "English" }}
      />,
    );

    const navigation = screen.getByRole("navigation", { name: "Language" });
    const bosnian = screen.getByRole("link", { name: "Bosanski" });
    const english = screen.getByRole("link", { name: "English" });

    expect(navigation.contains(bosnian)).toBe(true);
    expect(bosnian.getAttribute("href")).toBe("/bs/audits/6f1c2a8e-3b4d-4c5e-9f60-7a8b9c0d1e2f");
    expect(bosnian.hasAttribute("aria-current")).toBe(false);
    expect(english.getAttribute("aria-current")).toBe("true");
  });
});
