import { Link } from "react-router-dom";

type NavTabsProps = {
  insightsHref: string;
  inInsights: boolean;
};

export function NavTabs({ insightsHref, inInsights }: NavTabsProps) {
  return (
    <div className="flex items-center gap-3 mt-8">
      <Link
        className={
          inInsights
            ? "bg-black/40 border border-cyan/40 text-cyan text-sm font-semibold px-4 py-2 rounded-md"
            : "bg-neon text-black text-sm font-semibold px-4 py-2 rounded-md"
        }
        to="/"
      >
        Review Workspace
      </Link>
      <Link
        className={
          inInsights
            ? "bg-neon text-black text-sm font-semibold px-4 py-2 rounded-md"
            : "bg-black/40 border border-cyan/40 text-cyan text-sm font-semibold px-4 py-2 rounded-md"
        }
        to={insightsHref}
      >
        Insights & Chat
      </Link>
    </div>
  );
}
