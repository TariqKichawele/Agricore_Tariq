import { createTheme } from "@mui/material";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#2e7d32" },
    secondary: { main: "#558b2f" },
    background: { default: "#f4f7f4" },
  },
  shape: { borderRadius: 10 },
  typography: {
    h4: { fontWeight: 700 },
    h5: { fontWeight: 650 },
    h6: { fontWeight: 650 },
  },
});
