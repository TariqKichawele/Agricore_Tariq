import { useEffect, useState } from "react";
import { Box, Chip, Container, Paper, Typography } from "@mui/material";

type HealthState = "checking" | "ok" | "down";

export default function App() {
  const [health, setHealth] = useState<HealthState>("checking");
  const healthUrl = import.meta.env.VITE_API_HEALTH_URL ?? "http://localhost:8000/health";

  useEffect(() => {
    fetch(healthUrl)
      .then((res) => (res.ok ? setHealth("ok") : setHealth("down")))
      .catch(() => setHealth("down"));
  }, [healthUrl]);

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>
          AgriCore Command Center
        </Typography>
        <Typography color="text.secondary" paragraph>
          Prairie Crest Agricultural Cooperative — local scaffold (Slice 0).
        </Typography>
        <Box>
          <Chip
            label={
              health === "checking"
                ? "API: checking"
                : health === "ok"
                  ? "API: healthy"
                  : "API: unreachable"
            }
            color={health === "ok" ? "success" : health === "checking" ? "default" : "warning"}
          />
        </Box>
      </Paper>
    </Container>
  );
}
