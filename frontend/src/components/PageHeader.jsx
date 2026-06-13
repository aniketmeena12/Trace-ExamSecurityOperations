// Consistent dashboard hero: role icon badge + title + subtitle, optional
// right-aligned slot (status pill, identity, etc.).
import { IconBadge } from "./primitives";

export function PageHeader({ icon, iconTone = "secure", title, subtitle, right }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="flex items-center gap-4">
        <IconBadge icon={icon} tone={iconTone} size="lg" />
        <div>
          <h1 className="text-xl font-bold tracking-tight text-ink">{title}</h1>
          <p className="mt-0.5 max-w-xl text-sm text-muted">{subtitle}</p>
        </div>
      </div>
      {right && <div className="shrink-0">{right}</div>}
    </div>
  );
}
