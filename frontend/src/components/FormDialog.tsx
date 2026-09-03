import type { FormEvent, ReactNode } from "react";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from "@mui/material";

type FormDialogProps = {
  open: boolean;
  title: string;
  error: string | null;
  submitting: boolean;
  onClose: () => void;
  onSubmit: (event: FormEvent) => void;
  children: ReactNode;
  submitLabel?: string;
};

export function FormDialog({
  open,
  title,
  error,
  submitting,
  onClose,
  onSubmit,
  children,
  submitLabel = "Save",
}: FormDialogProps) {
  return (
    <Dialog open={open} onClose={submitting ? undefined : onClose} fullWidth maxWidth="sm">
      <form onSubmit={onSubmit}>
        <DialogTitle>{title}</DialogTitle>
        <DialogContent sx={{ display: "grid", gap: 2, pt: 1 }}>{error && <Alert severity="error">{error}</Alert>}{children}</DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={submitting}>
            {submitting ? "Saving…" : submitLabel}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
