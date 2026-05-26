import { Outlet } from "react-router-dom";
import { cn } from "@/lib/cn";
import { AppOverlays } from "./app-layout/app-overlays";
import { AppSidebar } from "./app-layout/app-sidebar";
import { AppTopBar } from "./app-layout/app-top-bar";
import { useAppLayoutController } from "./app-layout/use-app-layout-controller";
import { WorkflowDialogs } from "./app-layout/workflow-dialogs";

export function AppLayout() {
  const controller = useAppLayoutController();

  return (
    <div
      className={cn(
        "group/shell relative h-screen grid grid-cols-[244px_1fr] gap-[14px] z-10 data-[collapsed=true]:grid-cols-[64px_1fr]",
      )}
      data-collapsed={controller.collapsed}
    >
      <div className="dot-grid" />

      <AppSidebar controller={controller} />

      <div className="relative overflow-hidden h-screen pt-[14px] pr-[14px] pb-[14px] pl-0 flex flex-col">
        <div className="bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[16px] h-full overflow-hidden shadow-[inset_0_1px_0_oklch(0.30_0.004_250/0.4),0_24px_48px_-28px_oklch(0_0_0/0.6)] flex flex-col flex-1 min-h-0">
          <AppTopBar controller={controller} />
          <div
            className="flex-1 min-h-0 overflow-y-auto [&::-webkit-scrollbar]:hidden [scrollbar-width:none]"
            style={{ height: "100%" }}
          >
            <Outlet />
          </div>
        </div>
      </div>

      <AppOverlays controller={controller} />
      <WorkflowDialogs controller={controller} />
    </div>
  );
}
