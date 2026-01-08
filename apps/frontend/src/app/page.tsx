'use client';

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function UploadPage() {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);

  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setIsUploading(true);
    const form = e.currentTarget;
    const data = new FormData(form);

    try {
      const res = await fetch(`${API_BASE}/upload`, {method: 'POST', body: data});

      if(!res.ok) {
        const errorText = await res.text();
        setError(`Upload failed (${res.status}). ${errorText || 'Unknown error'}`);
        return;
      }

      const uploadData = await res.json();

      if(uploadData.workflow_started) {
        const runId = uploadData.run_id;
        if (runId) {
          router.push(`/dashboard?run=${runId}`);
        } else {
          router.push('/dashboard');
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      setError(
        `Failed to connect to API at ${API_BASE}. Make sure the backend server is running.`,
      );
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 px-6 py-10">
      <div className="mb-6">
        <Link
          href="/dashboard"
          className="inline-flex items-center rounded border px-3 py-1 text-sm font-medium text-gray-700"
        >
          Back to Dashboard
        </Link>
      </div>
      <div className="mx-auto max-w-lg rounded border bg-white p-6 shadow-sm">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold">
            Upload file for compliance review
          </h1>
          <p className="text-sm text-gray-600">
            Accepted formats: JSON or plain text. The workflow starts
            automatically after upload.
          </p>
        </div>

        <form onSubmit={handleUpload} className="mt-6 space-y-4">
          <label className="flex cursor-pointer flex-col items-center justify-center rounded border border-dashed border-gray-300 bg-gray-50 px-6 py-8 text-sm text-gray-600 transition hover:border-blue-300 hover:bg-blue-50">
            <span className="font-medium text-gray-800">
              Drag and drop a file or click to browse
            </span>
            <span className="mt-1 text-xs text-gray-500">
              Maximize clarity by uploading JSON exports or text files.
            </span>
            <input
              type="file"
              name="file"
              required
              className="sr-only"
              disabled={isUploading}
              onChange={(event) => {
                const file = event.currentTarget.files?.[0];
                setSelectedFileName(file ? file.name : null);
              }}
            />
          </label>

          <div className="text-xs text-gray-500">
            {selectedFileName ? `Selected file: ${selectedFileName}` : "No file selected yet."}
          </div>

          {error && (
            <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <button
              type="submit"
              className="inline-flex items-center justify-center rounded border border-blue-600 bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isUploading}
            >
              {isUploading ? 'Uploading...' : 'Upload & Start'}
            </button>
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center rounded border px-4 py-2 text-sm font-medium text-gray-700"
            >
              Go to Dashboard
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
