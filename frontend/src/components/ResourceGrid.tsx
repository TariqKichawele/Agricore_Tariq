import { Box, Button, Paper, Stack, Typography } from "@mui/material";
import { DataGrid, GridToolbar, type GridColDef } from "@mui/x-data-grid";
import type { ReactNode } from "react";

type ResourceGridProps = {
  title: string;
  rows: object[];
  columns: GridColDef[];
  loading: boolean;
  emptyLabel: string;
  headerAction?: ReactNode;
};

export function ResourceGrid({ title, rows, columns, loading, emptyLabel, headerAction }: ResourceGridProps) {
  return (
    <Paper sx={{ p: 2 }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }} gap={2}>
        <Typography variant="h5">{title}</Typography>
        {headerAction ? <Box>{headerAction}</Box> : null}
      </Stack>
      <DataGrid
        autoHeight
        rows={rows}
        columns={columns}
        loading={loading}
        disableRowSelectionOnClick
        pageSizeOptions={[10, 25, 50]}
        initialState={{
          pagination: { paginationModel: { pageSize: 10 } },
        }}
        slots={{ toolbar: GridToolbar }}
        slotProps={{
          toolbar: {
            showQuickFilter: true,
            quickFilterProps: { debounceMs: 300 },
          },
        }}
        localeText={{ noRowsLabel: emptyLabel }}
        sx={{
          border: 0,
          "& .MuiDataGrid-toolbarContainer": { pb: 1 },
        }}
      />
    </Paper>
  );
}

export function AddButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <Button variant="contained" onClick={onClick}>
      {label}
    </Button>
  );
}
