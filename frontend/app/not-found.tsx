import Link from "next/link";

export default function NotFound() {
  return (
    <main className="section">
      <div className="panel">
        <p className="eyebrow">404</p>
        <h1 style={{ marginTop: 0 }}>Not Found</h1>
        <p className="caption">The requested page or job manifest does not exist.</p>
        <div className="cta-row">
          <Link href="/" className="btn btn-primary">
            Back to Homepage
          </Link>
        </div>
      </div>
    </main>
  );
}
