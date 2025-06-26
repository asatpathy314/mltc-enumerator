import { ContextRequest, ContextEnumeration, VerifiedContext, ThreatEnumeration } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Debug logging for development
if (typeof window !== 'undefined') {
  console.log('API_BASE_URL:', API_BASE_URL);
  console.log('NEXT_PUBLIC_API_URL env var:', process.env.NEXT_PUBLIC_API_URL);
}

export async function postContext(request: ContextRequest): Promise<ContextEnumeration> {
  const response = await fetch(`${API_BASE_URL}/context`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to enumerate context: ${response.statusText}`);
  }

  return response.json();
}

export async function postGenerate(verifiedContext: VerifiedContext): Promise<ThreatEnumeration> {
  const response = await fetch(`${API_BASE_URL}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(verifiedContext),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate threats: ${response.statusText}`);
  }

  return response.json();
}

export async function ping(): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/ping`);
  
  if (!response.ok) {
    throw new Error(`Ping failed: ${response.statusText}`);
  }

  return response.json();
} 