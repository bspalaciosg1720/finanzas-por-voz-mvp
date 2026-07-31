import type { Metadata } from "next";

import "./styles.css";

export const metadata: Metadata = {
  title: "Clara — Tus finanzas, en tus palabras",
  description:
    "Registra gastos e ingresos hablando. Clara organiza tus movimientos, presupuestos y metas sin hojas de cálculo.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
