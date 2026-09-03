import { useState, type ReactNode } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Agriculture,
  Assignment,
  Dashboard,
  FactCheck,
  Logout,
  Menu as MenuIcon,
  People,
  PrecisionManufacturing,
  Warehouse,
} from "@mui/icons-material";
import {
  AppBar,
  Box,
  Chip,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useAuth } from "../context/AuthContext";
import { navForRole, ROLE_LABEL } from "../nav";

const DRAWER_WIDTH = 260;

const ICONS: Record<string, ReactNode> = {
  "/": <Dashboard />,
  "/farms": <Warehouse />,
  "/equipment": <PrecisionManufacturing />,
  "/jobs": <Assignment />,
  "/users": <People />,
  "/audit-logs": <FactCheck />,
};

export function AppLayout() {
  const theme = useTheme();
  const isMdUp = useMediaQuery(theme.breakpoints.up("md"));
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  if (!user) {
    return null;
  }

  const items = navForRole(user.role);
  const current = items.find((item) =>
    item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to),
  );

  const drawer = (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Toolbar sx={{ gap: 1.5, px: 2 }}>
        <Agriculture color="primary" />
        <Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
            AgriCore
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Prairie Crest Co-op
          </Typography>
        </Box>
      </Toolbar>
      <Divider />
      <List sx={{ px: 1, py: 1.5, flex: 1 }}>
        {items.map((item) => (
          <ListItemButton
            key={item.to}
            component={NavLink}
            to={item.to}
            end={item.to === "/"}
            onClick={() => setMobileOpen(false)}
            selected={
              item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to)
            }
            sx={{ borderRadius: 1.5, mb: 0.5 }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>{ICONS[item.to]}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
      <Divider />
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {user.full_name}
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          {user.email}
        </Typography>
        <Chip size="small" label={ROLE_LABEL[user.role]} sx={{ mt: 1 }} />
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar
        position="fixed"
        color="inherit"
        elevation={0}
        sx={{
          borderBottom: 1,
          borderColor: "divider",
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar>
          {!isMdUp && (
            <IconButton edge="start" onClick={() => setMobileOpen(true)} sx={{ mr: 1 }} aria-label="Open navigation">
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            {current?.label ?? "AgriCore"}
          </Typography>
          <IconButton
            color="inherit"
            onClick={() => {
              logout();
              navigate("/login", { replace: true });
            }}
            aria-label="Log out"
          >
            <Logout />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Box component="nav" sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}>
        {isMdUp ? (
          <Drawer
            variant="permanent"
            open
            sx={{
              "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box" },
            }}
          >
            {drawer}
          </Drawer>
        ) : (
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={() => setMobileOpen(false)}
            ModalProps={{ keepMounted: true }}
            sx={{
              "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box" },
            }}
          >
            {drawer}
          </Drawer>
        )}
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          bgcolor: "background.default",
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
