import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useReactFlow } from "reactflow";
import { useMutation } from "@tanstack/react-query";
import { useConfirm } from "@/shared/components/ConfirmModal";
import { APP_ROUTES } from "@/shared/constants/routes";
import { useWorkflowEditorStore } from "../../../stores/workflowEditorStore";
import { editorAPI } from "../../../services/editorAPI";

export function useInspectorHeaderMenu() {
  const navigate = useNavigate();
  const { fitView } = useReactFlow();
  const confirm = useConfirm();

  const workflow = useWorkflowEditorStore((s) => s.workflow);
  const workflowLocked = useWorkflowEditorStore((s) => s.workflowLocked);
  const toggleWorkflowLock = useWorkflowEditorStore(
    (s) => s.toggleWorkflowLock,
  );

  const onAutoLayout = useCallback(() => {
    fitView({ padding: 0.15, duration: 400 });
  }, [fitView]);

  const onExportWorkflow = useCallback(() => {
    if (!workflow) return;
    const blob = new Blob([JSON.stringify(workflow, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${workflow.name ?? "workflow"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [workflow]);

  const deleteMutation = useMutation({
    mutationFn: () => editorAPI.deleteWorkflow(workflow!.id),
    onSuccess: () => navigate(APP_ROUTES.AUTOMATIONS),
  });

  const onDeleteWorkflow = useCallback(async () => {
    const ok = await confirm({
      title: "Delete workflow",
      message: `"${workflow?.name ?? "This workflow"}" will be permanently deleted and cannot be recovered.`,
      confirmText: "Delete",
      variant: "danger",
    });
    if (ok) deleteMutation.mutate();
  }, [confirm, workflow, deleteMutation]);

  return {
    workflowLocked,
    onAutoLayout,
    onLockWorkflow: toggleWorkflowLock,
    onExportWorkflow,
    onDeleteWorkflow,
    isDeleting: deleteMutation.isPending,
  };
}
