import { describe, expect, it } from "vitest";
import { firstForwardedAddress } from "./client-ip";

describe("firstForwardedAddress", () => {
  it.each([
    ["203.0.113.7, 10.0.0.1", "203.0.113.7"],
    [" 2001:db8::1 ", "2001:db8::1"],
    ["", null],
    [null, null],
  ])("reads %j as %j", (header, expected) => {
    expect(firstForwardedAddress(header)).toBe(expected);
  });
});
