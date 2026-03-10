import type { HTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";

interface SparklineProps extends Omit<HTMLAttributes<SVGSVGElement>, "children"> {
  /** Numeric data points (minimum 1). Rendered left-to-right. */
  data: number[];
  /** ViewBox width in pixels — used for coordinate calculations only (default: 80) */
  width?: number;
  /** SVG height in pixels (default: 28) */
  height?: number;
  /** Stroke colour. Accepts any CSS colour or a Tailwind token var. Default: brand accent */
  strokeColor?: string;
  /** Stroke width in pixels (default: 2) */
  strokeWidth?: number;
  /** Whether to fill below the line with a subtle gradient (default: true) */
  showFill?: boolean;
}

export function Sparkline({
  data,
  width = 80,
  height = 28,
  strokeColor = "var(--color-action-primary)",
  strokeWidth = 2,
  showFill = true,
  className,
  "aria-label": ariaLabel,
  ...props
}: SparklineProps): JSX.Element {
  // Guard: empty / single-point
  if (data.length === 0) {
    return (
      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className={cn("block", className)}
        role="img"
        aria-label={ariaLabel ?? "No trend data"}
        {...props}
      />
    );
  }

  if (data.length === 1) {
    const cx = width / 2;
    const cy = height / 2;
    return (
      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className={cn("block", className)}
        role="img"
        aria-label={ariaLabel ?? `Single data point: ${data[0]}`}
        {...props}
      >
        <circle cx={cx} cy={cy} r={3} fill={strokeColor} />
      </svg>
    );
  }

  // Compute normalised points with padding
  const pad = strokeWidth + 1;
  const minVal = Math.min(...data);
  const maxVal = Math.max(...data);
  const range = maxVal - minVal || 1;

  const points = data.map((value, i) => {
    const x = pad + ((width - 2 * pad) * i) / (data.length - 1);
    const y = height - pad - ((height - 2 * pad) * (value - minVal)) / range;
    return { x, y };
  });

  const polylinePoints = points.map((p) => `${p.x},${p.y}`).join(" ");
  const gradientId = `sparkline-grad-${Math.random().toString(36).slice(2, 8)}`;

  // Closed polygon for the fill area (line + bottom edge)
  const fillPoints = [
    ...points.map((p) => `${p.x},${p.y}`),
    `${points[points.length - 1].x},${height}`,
    `${points[0].x},${height}`
  ].join(" ");

  return (
    <svg
      width="100%"
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className={cn("block", className)}
      role="img"
      aria-label={ariaLabel ?? `Trend: ${data.join(", ")}`}
      {...props}
    >
      {showFill && (
        <>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={strokeColor} stopOpacity={0.25} />
              <stop offset="100%" stopColor={strokeColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          <polygon points={fillPoints} fill={`url(#${gradientId})`} />
        </>
      )}
      <polyline
        points={polylinePoints}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* End-point dot */}
      <circle
        cx={points[points.length - 1].x}
        cy={points[points.length - 1].y}
        r={2.5}
        fill={strokeColor}
      />
    </svg>
  );
}
