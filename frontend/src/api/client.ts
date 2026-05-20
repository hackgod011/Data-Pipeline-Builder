import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// Attach JWT from localStorage on every request
api.interceptors.request.use((config) => {
  const raw = localStorage.getItem("pipeforge-auth");
  if (raw) {
    try {
      const state = JSON.parse(raw) as { state?: { token?: string } };
      const token = state?.state?.token;
      if (token) config.headers.Authorization = `Bearer ${token}`;
    } catch {
      // ignore malformed storage
    }
  }
  return config;
});

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export const authApi = {
  register: (email: string, password: string) =>
    api.post<AuthUser>("/api/v1/auth/register", { email, password }),
  login: (email: string, password: string) =>
    api.post<Token>("/api/v1/auth/login", { email, password }),
  me: (token: string) =>
    api.get<AuthUser>("/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    }),
};

// ─── Sources ─────────────────────────────────────────────────────────────────

export interface SchemaColumn {
  name: string;
  dtype: string;
  null_count: number;
  unique_count: number;
  sample_values: (string | number | null)[];
}

export interface DataSource {
  id: string;
  source_type: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  row_count: number | null;
  column_count: number | null;
  processing_status: "pending" | "processing" | "ready" | "error";
  processing_progress: number;
  processing_error: string | null;
  schema_columns: SchemaColumn[] | null;
  uploaded_at: string;
}

export const sourcesApi = {
  upload: (files: File[]) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return api.post<{ source_ids: string[]; status: string }>(
      "/api/v1/sources/upload",
      form,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
  },
  connectDb: (body: { db_type: string; connection_string: string; query?: string; name?: string }) =>
    api.post<{ source_ids: string[]; status: string }>("/api/v1/sources/connect", body),
  list: () => api.get<DataSource[]>("/api/v1/sources"),
  get: (id: string) => api.get<DataSource>(`/api/v1/sources/${id}`),
  preview: (id: string) =>
    api.get<{ columns: string[]; rows: Record<string, unknown>[]; total_rows: number }>(
      `/api/v1/sources/${id}/preview`
    ),
};

// ─── Pipelines ───────────────────────────────────────────────────────────────

export interface PipelineStep {
  step_id: string;
  type: "extract" | "transform" | "load" | "validate";
  operation: string;
  params: Record<string, unknown>;
  output_alias: string;
  description: string;
  depends_on: string[];
}

export interface PipelinePlan {
  pipeline_id: string;
  name: string;
  nl_prompt: string;
  version: number;
  steps: PipelineStep[];
}

export interface GenerateResponse {
  pipeline_id: string;
  plan: PipelinePlan | null;
  generated_code: string | null;
  clarifying_questions: string[];
}

export interface Pipeline {
  id: string;
  name: string;
  nl_prompt: string;
  plan: PipelinePlan;
  generated_code: string | null;
  code_mode: "pandas" | "sql";
  version: number;
  created_at: string;
  updated_at: string;
}

export const pipelinesApi = {
  generate: (body: { nl_prompt: string; source_ids: string[]; pipeline_name?: string; code_mode?: "pandas" | "sql" }) =>
    api.post<GenerateResponse>("/api/v1/pipelines/generate", body),
  list: () => api.get<Pipeline[]>("/api/v1/pipelines"),
  get: (id: string) => api.get<Pipeline>(`/api/v1/pipelines/${id}`),
  getCode: (id: string) =>
    api.get<{ code: string; mode: string }>(`/api/v1/pipelines/${id}/code`),
  update: (id: string, body: { plan: PipelinePlan; code_mode: string }) =>
    api.put<Pipeline>(`/api/v1/pipelines/${id}`, body),
  exportUrl: (id: string) =>
    `${api.defaults.baseURL ?? "http://localhost:8000"}/api/v1/pipelines/${id}/export`,
};

// ─── Executions ──────────────────────────────────────────────────────────────

export interface StepLog {
  step_id: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
  rows_in: number | null;
  rows_out: number | null;
  message: string;
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  null_count: number;
  null_pct: number;
  unique_count: number;
  unique_pct: number;
  min: number | null;
  max: number | null;
  mean: number | null;
  std: number | null;
  sample_values: (string | number | null)[];
}

export interface ProfileResult {
  row_count: number;
  column_count: number;
  quality_score: number;
  columns: ColumnProfile[];
}

export interface Execution {
  id: string;
  pipeline_id: string;
  status: "pending" | "running" | "success" | "failed";
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  step_logs: StepLog[] | null;
  output_file_path: string | null;
  output_profile: ProfileResult | null;
  created_at: string;
}

export const executionsApi = {
  execute: (pipelineId: string) =>
    api.post<{ execution_id: string; status: string }>(
      `/api/v1/pipelines/${pipelineId}/execute`
    ),
  get: (id: string) => api.get<Execution>(`/api/v1/executions/${id}`),
  listForPipeline: (pipelineId: string) =>
    api.get<Execution[]>(`/api/v1/pipelines/${pipelineId}/executions`),
};

// ─── Schedules ───────────────────────────────────────────────────────────────

export interface Schedule {
  id: string;
  pipeline_id: string;
  pipeline_name: string | null;
  cron_expression: string;
  is_active: boolean;
  created_at: string;
  last_run_at: string | null;
  next_run_at: string | null;
}

export const schedulesApi = {
  upsert: (pipelineId: string, cron_expression: string) =>
    api.put<Schedule>(`/api/v1/schedules/pipelines/${pipelineId}`, { cron_expression }),
  remove: (pipelineId: string) =>
    api.delete(`/api/v1/schedules/pipelines/${pipelineId}`),
  getForPipeline: (pipelineId: string) =>
    api.get<Schedule>(`/api/v1/schedules/pipelines/${pipelineId}`),
  list: () => api.get<Schedule[]>("/api/v1/schedules"),
  toggle: (scheduleId: string) =>
    api.patch<Schedule>(`/api/v1/schedules/${scheduleId}/toggle`),
};
