import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LanguageSwitcher } from "./language-switcher";

describe("LanguageSwitcher", () => {
  it("links to every locale and marks the current one", () => {
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
    expect(bosnian.getAttribute("href")).toBe("/bs");
    expect(bosnian.hasAttribute("aria-current")).toBe(false);
    expect(english.getAttribute("href")).toBe("/en");
    expect(english.getAttribute("aria-current")).toBe("true");
  });
});
