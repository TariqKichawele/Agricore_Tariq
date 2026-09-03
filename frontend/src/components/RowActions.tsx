import type { ReactNode } from "react";
import { IconButton, Stack } from "@mui/material";
import { Delete, Edit } from "@mui/icons-material";

type RowActionsProps = {
  onEdit?: () => void;
  onDelete?: () => void;
  extra?: ReactNode;
};

export function RowActions({ onEdit, onDelete, extra }: RowActionsProps) {
  return (
    <Stack direction="row" spacing={0.5} alignItems="center">
      {extra}
      {onEdit && (
        <IconButton size="small" aria-label="Edit" onClick={onEdit}>
          <Edit fontSize="small" />
        </IconButton>
      )}
      {onDelete && (
        <IconButton size="small" aria-label="Delete" onClick={onDelete} color="error">
          <Delete fontSize="small" />
        </IconButton>
      )}
    </Stack>
  );
}
