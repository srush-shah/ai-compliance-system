'use client';

export default function UploadPage() {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget;
    const data = new FormData(form);

    await fetch(`${API_BASE}/upload`, {method: 'POST', body: data});

    alert('Uploaded');
  }

  return (
    <form onSubmit={handleUpload} className="p-6 space-y-4">
      <input type="file" name="file" required />
      <button className="border px-4 py-2">Upload</button>
    </form>
  );
}