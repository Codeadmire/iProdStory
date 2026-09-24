/**
 * Central API client.
 * All fetch calls go through here — never hardcode localhost in components.
 */
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface RequestOptions extends RequestInit {
  token?: string;
  workspaceId?: string;
}

async function request<T = unknown>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, workspaceId, headers: extraHeaders, ...rest } = options;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(extraHeaders as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (workspaceId) headers["X-Workspace-Id"] = workspaceId;

  const res = await fetch(`${BASE_URL}${path}`, { headers, ...rest });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get:    <T = unknown>(path: string, opts?: RequestOptions) => request<T>(path, { method: "GET", ...opts }),
  post:   <T = unknown>(path: string, body?: unknown, opts?: RequestOptions) => request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined, ...opts }),
  put:    <T = unknown>(path: string, body?: unknown, opts?: RequestOptions) => request<T>(path, { method: "PUT", body: body !== undefined ? JSON.stringify(body) : undefined, ...opts }),
  delete: <T = unknown>(path: string, opts?: RequestOptions) => request<T>(path, { method: "DELETE", ...opts }),
  mediaUrl: (key: string) => `${BASE_URL}/media/${key}`,
};

export { BASE_URL };
