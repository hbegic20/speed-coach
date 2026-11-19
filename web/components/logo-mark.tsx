type LogoMarkProps = {
  size: number;
};

export function LogoMark({ size }: LogoMarkProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="8" className="fill-accent" />
      <path
        d="M8 20a8 8 0 0 1 16 0"
        fill="none"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path d="M16 20l5-6" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}
