import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: { default: "PaceForge", template: "%s · PaceForge" },
  description: "Personal fitness training — running, lifting, mobility",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "PaceForge",
  },
  formatDetection: { telephone: false },
  icons: {
    icon: "/icons/icon-192.png",
    apple: "/icons/icon-192.png",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",       // essential for iPhone notch / Dynamic Island
  themeColor: [
    { media: "(prefers-color-scheme: dark)",  color: "#050a14" },
    { media: "(prefers-color-scheme: light)", color: "#f8fafc" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans min-h-screen bg-background text-foreground antialiased`}>
        <Providers>{children}</Providers>
        {/* SW registration */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js')
                    .then(function(reg) {
                      // Listen for offline-queue sync messages from SW
                      navigator.serviceWorker.addEventListener('message', function(e) {
                        if (e.data && e.data.type === 'SYNC_OFFLINE_QUEUE') {
                          window.dispatchEvent(new CustomEvent('paceforge:sync-offline'));
                        }
                      });
                    })
                    .catch(function(err) { console.warn('SW registration failed:', err); });
                });
              }
            `,
          }}
        />
      </body>
    </html>
  );
}
