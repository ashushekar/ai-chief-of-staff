import './globals.css';

export const metadata = {
  title: 'AI Chief of Staff',
  description: 'Gemini-powered morning triage, email drafting, and decision support',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
