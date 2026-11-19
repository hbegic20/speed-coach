const SCHEME = /^[a-z][a-z\d+\-.]*:\/\//i;

export function normalizeUrlInput(input: string): string {
  const trimmed = input.trim();
  if (trimmed === "" || SCHEME.test(trimmed)) return trimmed;
  return `https://${trimmed}`;
}
