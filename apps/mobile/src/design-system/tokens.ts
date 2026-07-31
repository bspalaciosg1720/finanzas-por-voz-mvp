import type { TextStyle } from "react-native";

export const colors = {
  background: "#F4F5F2",
  surface: "#FFFFFF",
  ink: "#202624",
  muted: "#68716D",
  border: "#DFE4E0",
  primary: "#245B62",
  primarySoft: "#E8F0F0",
  olive: "#788665",
  danger: "#A34D4D",
  onPrimaryMuted: "#D7E4E5",
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const;

export const radius = {
  sm: 10,
  md: 16,
  lg: 20,
  round: 999,
} as const;

export const typography = {
  title: {
    fontSize: 28,
    fontWeight: "700",
    letterSpacing: -0.8,
  },
  amount: {
    fontSize: 32,
    fontWeight: "700",
    letterSpacing: -1,
  },
  cardValue: {
    fontSize: 17,
    fontWeight: "700",
  },
  body: {
    fontSize: 16,
    fontWeight: "400",
  },
  button: {
    fontSize: 16,
    fontWeight: "700",
  },
  label: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1,
  },
  caption: {
    fontSize: 12,
    fontWeight: "400",
  },
} satisfies Record<string, TextStyle>;

