import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/lib/providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MLTC Enumerator",
  description: "Security threat modeling tool",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Providers>
          <div className="min-h-screen flex flex-col">
            <header className="border-b">
              <div className="container mx-auto py-4">
                <nav className="flex items-center justify-between">
                  <div className="font-semibold text-xl">MLTC Enumerator</div>
                  <div className="flex gap-4">
                    <a href="/" className="hover:underline">Home</a>
                    <a href="/context" className="hover:underline">Context</a>
                    <a href="/threats" className="hover:underline">Threats</a>
                  </div>
                </nav>
              </div>
            </header>
            <main className="flex-1 container mx-auto py-8">
              {children}
            </main>
            <footer className="border-t">
              <div className="container mx-auto py-4 text-center text-sm text-gray-500">
                © {new Date().getFullYear()} MLTC Enumerator
              </div>
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
