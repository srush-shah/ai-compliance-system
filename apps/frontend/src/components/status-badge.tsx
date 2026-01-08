type StatusBadgeProps = {
  label: string;
  tone: "blue" | "green" | "red" | "gray" | "yellow";
};

const toneClasses: Record<StatusBadgeProps["tone"], string> = {
  blue: "bg-blue-100 text-blue-700 border-blue-200",
  green: "bg-green-100 text-green-700 border-green-200",
  red: "bg-red-100 text-red-700 border-red-200",
  gray: "bg-gray-100 text-gray-700 border-gray-200",
  yellow: "bg-yellow-100 text-yellow-700 border-yellow-200",
};

export default function StatusBadge({ label, tone }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${toneClasses[tone]}`}
    >
      {label}
    </span>
  );
}
