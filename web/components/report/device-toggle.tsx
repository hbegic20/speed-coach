import Link from "next/link";
import { devices, type Device } from "@/lib/api/schemas";

type DeviceToggleProps = {
  current: Device;
  basePath: string;
  groupLabel: string;
  deviceLabels: Record<Device, string>;
};

export function DeviceToggle({ current, basePath, groupLabel, deviceLabels }: DeviceToggleProps) {
  return (
    <nav aria-label={groupLabel}>
      <ul className="flex gap-1 rounded-[10px] bg-slate-200 p-1">
        {devices.map((device) => (
          <li key={device}>
            <Link
              href={device === "mobile" ? basePath : `${basePath}?device=${device}`}
              replace
              scroll={false}
              aria-current={device === current ? "page" : undefined}
              className="inline-flex min-h-11 items-center rounded-lg px-3.5 font-semibold text-slate-700 hover:text-ink aria-[current=page]:bg-white aria-[current=page]:text-ink aria-[current=page]:shadow-sm"
            >
              {deviceLabels[device]}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
