/**
 * Wordmark inspired by the radj charte (lowercase, tilde on j, baseline emphasis).
 * Swap font files in index.html to TS Deniz / 29LT Adir when licensed.
 */
type Props = {
  variant?: "limeOnNavy" | "navyOnLime" | "lime" | "navy";
  size?: "sm" | "md" | "lg";
  className?: string;
};

const sizes = {
  sm: "text-lg",
  md: "text-2xl",
  lg: "text-3xl md:text-4xl",
};

export default function RadjWordmark({ variant = "limeOnNavy", size = "md", className = "" }: Props) {
  const palette =
    variant === "navyOnLime"
      ? { word: "text-radj-lime", tilde: "text-radj-lime", line: "border-radj-lime" }
      : variant === "lime"
        ? { word: "text-radj-navy", tilde: "text-radj-navy", line: "border-radj-navy" }
        : variant === "navy"
          ? { word: "text-radj-lime", tilde: "text-radj-lime", line: "border-radj-lime" }
          : { word: "text-radj-navy", tilde: "text-radj-navy", line: "border-radj-navy" };

  return (
    <span className={`inline-block font-display font-bold leading-none tracking-tight ${sizes[size]} ${className}`}>
      <span className={`inline-flex items-end border-b-[3px] ${palette.line} pb-0.5 ${palette.word}`}>
        <span>rad</span>
        <span className={`relative inline-block ${palette.word}`}>
          <span
            className={`pointer-events-none absolute -top-[0.55em] left-1/2 -translate-x-1/2 font-sans text-[0.38em] font-normal leading-none ${palette.tilde}`}
            aria-hidden
          >
            ~
          </span>
          j
        </span>
      </span>
    </span>
  );
}
