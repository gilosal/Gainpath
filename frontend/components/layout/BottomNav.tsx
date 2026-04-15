"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CalendarDays, BarChart2, Settings, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/today",    label: "Today",    Icon: Sun         },
  { href: "/calendar", label: "Calendar", Icon: CalendarDays },
  { href: "/progress", label: "Progress", Icon: BarChart2   },
  { href: "/settings", label: "Settings", Icon: Settings    },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav
      className={cn(
        "fixed bottom-0 inset-x-0 z-50",
        "bg-card/95 backdrop-blur-md border-t border-border",
        "pb-safe" // handles iOS safe area
      )}
    >
      <ul className="flex h-16 items-stretch">
        {NAV_ITEMS.map(({ href, label, Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <li key={href} className="flex-1">
              <Link
                href={href}
                className={cn(
                  "flex flex-col items-center justify-center gap-0.5 h-full w-full",
                  "touch-target transition-colors duration-150",
                  active
                    ? "text-primary"
                    : "text-muted-foreground active:text-foreground"
                )}
              >
                <Icon
                  size={22}
                  strokeWidth={active ? 2.5 : 1.8}
                  className="transition-transform duration-150 active:scale-90"
                />
                <span className={cn("text-[10px] font-medium", active && "font-semibold")}>
                  {label}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
