'use client';

import { useRouter } from "next/navigation";

export default function UploadPage() {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const router = useRouter()

  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget;
    const data = new FormData(form);

    try {
      const res = await fetch(`${API_BASE}/upload`, {method: 'POST', body: data});

      if(!res.ok) {
        const errorText = await res.text();
        alert(`Upload failed! Status: ${res.status}. ${errorText || 'Unknown error'}`);
        return;
      }

      const uploadData = await res.json()

      if(uploadData.workflow_started) {
        router.push('/dashboard')
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert(`Failed to connect to API at ${API_BASE}. Make sure the backend server is running.`);
    }
  }

  return (
    <form onSubmit={handleUpload} className="p-6 space-y-4">
      <input type="file" name="file" required />
      <button className="border px-4 py-2">Upload</button>
    </form>
  );
}