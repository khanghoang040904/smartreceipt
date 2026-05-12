const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request(path: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401 && !path.startsWith("/api/auth/")) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
  }
  return res;
}

// Auth
export async function apiRegister(email: string, fullName: string, password: string) {
  const res = await request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, full_name: fullName, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

export async function apiLogin(email: string, password: string) {
  const res = await request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Login failed");
  }
  return res.json();
}

export async function apiGetMe() {
  const res = await request("/api/auth/me");
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

// Receipts
export async function apiUploadReceipt(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await request("/api/receipts/upload", {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function apiGetReceipts(params?: {
  search?: string;
  category_id?: number;
  date_from?: string;
  date_to?: string;
}) {
  const query = new URLSearchParams();
  if (params?.search) query.set("search", params.search);
  if (params?.category_id) query.set("category_id", String(params.category_id));
  if (params?.date_from) query.set("date_from", params.date_from);
  if (params?.date_to) query.set("date_to", params.date_to);

  const qs = query.toString();
  const res = await request(`/api/receipts${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error("Failed to fetch receipts");
  return res.json();
}

export async function apiGetReceipt(id: number) {
  const res = await request(`/api/receipts/${id}`);
  if (!res.ok) throw new Error("Failed to fetch receipt");
  return res.json();
}

export async function apiUpdateReceipt(id: number, data: Record<string, unknown>) {
  const res = await request(`/api/receipts/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update receipt");
  return res.json();
}

export async function apiDeleteReceipt(id: number) {
  const res = await request(`/api/receipts/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete receipt");
  return res.json();
}

// Categories
export async function apiGetCategories() {
  const res = await request("/api/categories");
  if (!res.ok) throw new Error("Failed to fetch categories");
  return res.json();
}

export async function apiCreateCategory(name: string) {
  const res = await request("/api/categories", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error("Failed to create category");
  return res.json();
}

export async function apiDeleteCategory(id: number) {
  const res = await request(`/api/categories/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete category");
  return res.json();
}

// Dashboard
export async function apiGetDashboard() {
  const res = await request("/api/dashboard");
  if (!res.ok) throw new Error("Failed to fetch dashboard");
  return res.json();
}

// Export
export async function apiExportCSV() {
  const res = await request("/api/export/csv");
  if (!res.ok) throw new Error("Failed to export CSV");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "receipts_export.csv";
  a.click();
  URL.revokeObjectURL(url);
}

// Image URL helper
export function getImageUrl(imagePath: string): string {
  return `${API_BASE}/uploads/${imagePath}`;
}
