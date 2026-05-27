const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

type ApiRequestOptions = RequestInit & {
  skipAuthRedirect?: boolean;
};

async function request(path: string, options: ApiRequestOptions = {}): Promise<Response> {
  const { skipAuthRedirect, ...fetchOptions } = options;
  const token = getToken();
  const headers: Record<string, string> = {
    ...(fetchOptions.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (!(fetchOptions.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...fetchOptions, headers });
  if (res.status === 401 && !skipAuthRedirect) {
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
    skipAuthRedirect: true,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Không đăng ký được tài khoản");
  }
  return res.json();
}

export async function apiLogin(email: string, password: string) {
  const res = await request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    skipAuthRedirect: true,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Không đăng nhập được");
  }
  return res.json();
}

export async function apiGetMe() {
  const res = await request("/api/auth/me");
  if (!res.ok) throw new Error("Chưa đăng nhập");
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
    throw new Error(err.detail || "Không tải được hóa đơn");
  }
  return res.json();
}

export async function apiBatchUploadReceipts(files: File[]) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  const res = await request("/api/receipts/batch-upload", {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Không tải được hóa đơn");
  }
  return res.json();
}

export async function apiGetReceipts(params?: {
  search?: string;
  category_id?: number;
  date_from?: string;
  date_to?: string;
  status?: string;
}) {
  const query = new URLSearchParams();
  if (params?.search) query.set("search", params.search);
  if (params?.category_id) query.set("category_id", String(params.category_id));
  if (params?.date_from) query.set("date_from", params.date_from);
  if (params?.date_to) query.set("date_to", params.date_to);
  if (params?.status) query.set("status", params.status);

  const qs = query.toString();
  const res = await request(`/api/receipts${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error("Không tải được danh sách hóa đơn");
  return res.json();
}

export async function apiGetReceipt(id: number) {
  const res = await request(`/api/receipts/${id}`);
  if (!res.ok) throw new Error("Không tải được hóa đơn");
  return res.json();
}

export async function apiUpdateReceipt(id: number, data: Record<string, unknown>) {
  const res = await request(`/api/receipts/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Không cập nhật được hóa đơn");
  }
  return res.json();
}

export async function apiDeleteReceipt(id: number) {
  const res = await request(`/api/receipts/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Không xóa được hóa đơn");
  return res.json();
}

// Chat
export interface ChatSource {
  receipt_id: number;
  supplier_name: string | null;
  receipt_date: string | null;
  total_amount: number;
  image_url: string;
  chunk_text: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  route: string;
  sources: ChatSource[];
  sql_result: Record<string, unknown> | null;
  confidence: number;
}

export async function apiChat(message: string, filters?: {
  receipt_ids?: number[];
  date_from?: string;
  date_to?: string;
  category_id?: number;
}): Promise<ChatResponse> {
  const res = await request("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, ...filters }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Không gửi được câu hỏi");
  }
  return res.json();
}

export async function apiReindexChat() {
  const res = await request("/api/chat/reindex", { method: "POST" });
  if (!res.ok) throw new Error("Không làm mới được dữ liệu chat");
  return res.json();
}

// Categories
export async function apiGetCategories() {
  const res = await request("/api/categories");
  if (!res.ok) throw new Error("Không tải được danh mục");
  return res.json();
}

export async function apiCreateCategory(name: string) {
  const res = await request("/api/categories", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error("Không tạo được danh mục");
  return res.json();
}

export async function apiDeleteCategory(id: number) {
  const res = await request(`/api/categories/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Không xóa được danh mục");
  return res.json();
}

// Budgets
export interface BudgetCategorySummary {
  budget_id: number | null;
  category_id: number;
  category_name: string;
  month: string;
  budget_amount: number;
  spent_amount: number;
  remaining_amount: number;
  usage_percent: number;
  status: "unset" | "ok" | "warning" | "over";
}

export interface BudgetSummary {
  month: string;
  total_budget: number;
  total_spent: number;
  total_remaining: number;
  categories: BudgetCategorySummary[];
}

export async function apiGetBudgets(month: string): Promise<BudgetSummary> {
  const res = await request(`/api/budgets?month=${encodeURIComponent(month)}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Không tải được ngân sách");
  }
  return res.json();
}

export async function apiUpsertBudget(data: {
  category_id: number;
  month: string;
  amount: number;
}): Promise<BudgetCategorySummary> {
  const res = await request("/api/budgets", {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Không lưu được ngân sách");
  }
  return res.json();
}

export async function apiDeleteBudget(id: number) {
  const res = await request(`/api/budgets/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Không xóa được ngân sách");
  }
  return res.json();
}

// Dashboard
export async function apiGetDashboard() {
  const res = await request("/api/dashboard");
  if (!res.ok) throw new Error("Không tải được trang tổng quan");
  return res.json();
}

// Export
export async function apiExportCSV() {
  const res = await request("/api/export/csv");
  if (!res.ok) throw new Error("Không xuất được CSV");
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
