const API_URL = "http://127.0.0.1:8000";
const API_BASE_URL = 'http://127.0.0.1:8000'

export const STATUSES = [
  'Applied',
  'Interview',
  'Offer',
  'Rejected',
] as const

export type ApplicationStatus = (typeof STATUSES)[number]

export type Application = {
  id: number
  company: string
  role: string
  status: ApplicationStatus
  location?: string
  date?: string
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function listApplications(): Promise<Application[]> {
  return request<Application[]>('/api/applications')
}

export function createApplication(data: {
  company: string
  role: string
  status: ApplicationStatus
}): Promise<Application> {
  return request<Application>('/api/applications', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateApplicationStatus(
  id: number,
  status: ApplicationStatus,
): Promise<Application> {
  return request<Application>(`/api/applications/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}


export async function deleteApplication(id: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/applications/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("Could not delete the application");
  }
}

