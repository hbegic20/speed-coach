import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { getDictionary } from "@/lib/i18n/dictionaries";
import type { AuditFormState } from "@/app/[lang]/actions";
import { AuditForm } from "./audit-form";

const { form } = getDictionary("en");

describe("AuditForm", () => {
  it("has a labelled url field and a submit button", () => {
    render(<AuditForm action={async (state) => state} labels={form} variant="hero" />);

    expect(screen.getByLabelText("Website URL")).toBeDefined();
    expect(screen.getByRole("button", { name: "Analyze" })).toBeDefined();
  });

  it("shows the action's error next to the field and keeps the typed url", async () => {
    const rejectUrl = async (_state: AuditFormState, formData: FormData) => ({
      error: "invalid_url" as const,
      url: String(formData.get("url")),
    });
    render(<AuditForm action={rejectUrl} labels={form} variant="hero" />);
    const input = screen.getByLabelText("Website URL");

    fireEvent.change(input, { target: { value: "not a site" } });
    fireEvent.submit(input.closest("form") as HTMLFormElement);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toBe(form.errors.invalid_url);
    const updatedInput = screen.getByLabelText("Website URL");
    expect(updatedInput.getAttribute("aria-invalid")).toBe("true");
    expect(updatedInput.getAttribute("aria-describedby")).toBe(alert.id);
    expect((updatedInput as HTMLInputElement).value).toBe("not a site");
  });

  it("prefills the compact re-run form with the audited url", () => {
    render(
      <AuditForm
        action={async (state) => state}
        labels={{ ...form, submit: form.rerun }}
        variant="compact"
        initialUrl="https://example.ba/"
      />,
    );

    expect((screen.getByLabelText("Website URL") as HTMLInputElement).value).toBe(
      "https://example.ba/",
    );
    expect(screen.getByRole("button", { name: "Re-run" })).toBeDefined();
  });
});
