
const API_URL =
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export const STATUSES = [
  "Applied",
  "Interview",
  "Offer",
  "Rejected",
] as const;

export type ApplicationStatus = (typeof STATUSES)[number];

export type Application = {
  id: number;
  company: string;
  role: string;
  status: ApplicationStatus;
  location: string;
  date_added: string;
};

export type CreateApplicationData = {
  company: string;
  role: string;
  status?: ApplicationStatus;
  location?: string;
};


async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = sessionStorage.getItem("applyflow_token");

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function listApplications(
  signal?: AbortSignal,
): Promise<Application[]> {
  return request<Application[]>("/api/applications", {
    signal,
  });
}

export function createApplication(
  data: CreateApplicationData,
): Promise<Application> {
  return request<Application>("/api/applications", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateApplicationStatus(
  id: number,
  status: ApplicationStatus,
): Promise<Application> {
  return request<Application>(`/api/applications/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}


export async function deleteApplication(
  id: number,
): Promise<void> {
  const token = sessionStorage.getItem("applyflow_token");

  const response = await fetch(
    `${API_URL}/api/applications/${id}`,
    {
      method: "DELETE",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Could not delete the application: ${response.status}`,
    );
  }
}


export type AuthResponse = {
  access_token: string;
  token_type: string;
};

export type UserResponse = {
  id: number;
  email: string;
};

export async function registerUser(
  email: string,
  password: string,
): Promise<UserResponse> {
  return request<UserResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function loginUser(
  email: string,
  password: string,
): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}


export function saveToken(token: string): void {
  sessionStorage.setItem("applyflow_token", token);
}

export function getToken(): string | null {
  return sessionStorage.getItem("applyflow_token");
}

export function logoutUser(): void {
  sessionStorage.removeItem("applyflow_token");
}
