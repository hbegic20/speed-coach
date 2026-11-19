import { describe, expect, it } from "vitest";
import { recommendation } from "@/test/audit-fixture";
import { canMarkFix, fixStatus } from "./fix-status";

const CHECKED_AT = "2026-11-17T06:00:00Z";
const BEFORE_CHECK = "2026-11-16T10:00:00Z";
const AFTER_CHECK = "2026-11-18T10:00:00Z";

const merged = recommendation({ lighthouse_ids: ["render-blocking-resources", "unused-css"] });

describe("fixStatus", () => {
  it("is open until every problem behind the fix is marked", () => {
    const partly = [{ lighthouse_id: "unused-css", completed_at: AFTER_CHECK }];

    expect(fixStatus(merged, CHECKED_AT, [])).toBe("open");
    expect(fixStatus(merged, CHECKED_AT, partly)).toBe("open");
  });

  it("is done when it was marked after this check", () => {
    const marks = merged.lighthouse_ids.map((id) => ({ lighthouse_id: id, completed_at: AFTER_CHECK }));

    expect(fixStatus(merged, CHECKED_AT, marks)).toBe("done");
  });

  it("is still detected when a check after the mark found it again", () => {
    const marks = [
      { lighthouse_id: "render-blocking-resources", completed_at: AFTER_CHECK },
      { lighthouse_id: "unused-css", completed_at: BEFORE_CHECK },
    ];

    expect(fixStatus(merged, CHECKED_AT, marks)).toBe("stillDetected");
  });
});

describe("canMarkFix", () => {
  it("needs at least one lighthouse problem", () => {
    expect(canMarkFix(merged)).toBe(true);
    expect(canMarkFix(recommendation({ lighthouse_ids: [] }))).toBe(false);
  });
});
