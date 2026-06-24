import type { Metadata } from "next";
import { Lexend, Source_Sans_3 } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";

const lexend = Lexend({
  variable: "--font-lexend",
  subsets: ["latin"],
  display: "swap",
});

const sourceSans = Source_Sans_3({
  variable: "--font-source-sans",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "PolicyPulse AI — Evidence-first policy consultation",
  description:
    "Turn policy documents and public feedback into traceable concerns, gaps, and practical recommendations.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${lexend.variable} ${sourceSans.variable}`}>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}

