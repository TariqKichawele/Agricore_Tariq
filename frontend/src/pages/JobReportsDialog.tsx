import { FormEvent, useEffect, useState } from "react";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Link,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { listReports, uploadReport } from "../api/mutations";
import { errorMessage } from "../api/http";
import type { FieldJob, ServiceReport } from "../types";

type JobReportsDialogProps = {
  job: FieldJob | null;
  canUpload: boolean;
  onClose: () => void;
};

export function JobReportsDialog({ job, canUpload, onClose }: JobReportsDialogProps) {
  const [reports, setReports] = useState<ServiceReport[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (!job) {
      setReports([]);
      setFile(null);
      setNotes("");
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    listReports(job.id)
      .then((rows) => {
        if (!cancelled) {
          setReports(rows);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(errorMessage(err, "Could not load reports."));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [job]);

  async function onUpload(event: FormEvent) {
    event.preventDefault();
    if (!job || !file) {
      setError("Choose a file to upload.");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const created = await uploadReport(job.id, file, notes);
      setReports((current) => [created, ...current]);
      setFile(null);
      setNotes("");
    } catch (err) {
      setError(errorMessage(err, "Could not upload the report."));
    } finally {
      setUploading(false);
    }
  }

  return (
    <Dialog open={Boolean(job)} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Service reports{job ? ` — ${job.title}` : ""}</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {loading && <Typography color="text.secondary">Loading…</Typography>}
        {!loading && reports.length === 0 && (
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            No reports attached yet.
          </Typography>
        )}
        <Stack spacing={1.5} sx={{ mb: canUpload ? 3 : 0 }}>
          {reports.map((report) => (
            <Stack key={report.id} spacing={0.25}>
              <Link href={report.file_url} target="_blank" rel="noreferrer">
                Download file
              </Link>
              <Typography variant="caption" color="text.secondary">
                {new Date(report.created_at).toLocaleString()}
                {report.notes ? ` — ${report.notes}` : ""} · link expires in {Math.round(report.download_expires_in / 60)} min
              </Typography>
            </Stack>
          ))}
        </Stack>
        {canUpload && (
          <Stack component="form" spacing={2} onSubmit={onUpload}>
            <Button variant="outlined" component="label">
              {file ? file.name : "Choose file (image, .txt, or .pdf)"}
              <input
                hidden
                type="file"
                accept="image/*,.txt,.pdf,text/plain,application/pdf"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </Button>
            <TextField
              label="Notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              multiline
              minRows={2}
              fullWidth
            />
            <Button type="submit" variant="contained" disabled={uploading || !file}>
              {uploading ? "Uploading…" : "Upload report"}
            </Button>
          </Stack>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
