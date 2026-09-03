import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";

type ConfirmDialogProps = {
  open: boolean;
  title: string;
  body: string;
  confirmLabel?: string;
  onClose: () => void;
  onConfirm: () => void;
  busy?: boolean;
};

export function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel = "Delete",
  onClose,
  onConfirm,
  busy,
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onClose={busy ? undefined : onClose} fullWidth maxWidth="xs">
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Typography>{body}</Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={busy}>
          Cancel
        </Button>
        <Button color="error" variant="contained" onClick={onConfirm} disabled={busy}>
          {busy ? "Working…" : confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
