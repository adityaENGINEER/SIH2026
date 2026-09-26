export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  public status: number;
  public data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function handleResponse(response: Response) {
  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    throw new ApiError(
      response.status,
      errorData.detail || errorData.message || 'API request failed',
      errorData
    );
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  // Check content type to see if it's JSON
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }

  // Otherwise, return blob for file downloads
  return response.blob();
}

export const api = {
  get: async (endpoint: string, options: RequestInit = {}) => {
    const response = await fetch(`${API_BASE_URL}/api${endpoint}`, {
      ...options,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    return handleResponse(response);
  },

  post: async (endpoint: string, body: any, options: RequestInit = {}) => {
    const isFormData = body instanceof FormData;
    const headers: Record<string, string> = {
      ...(!isFormData && { 'Content-Type': 'application/json' }),
      ...(options.headers as any),
    };

    const response = await fetch(`${API_BASE_URL}/api${endpoint}`, {
      ...options,
      method: 'POST',
      headers,
      body: isFormData ? body : JSON.stringify(body),
    });
    return handleResponse(response);
  },

  patch: async (endpoint: string, body: any, options: RequestInit = {}) => {
    const response = await fetch(`${API_BASE_URL}/api${endpoint}`, {
      ...options,
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: JSON.stringify(body),
    });
    return handleResponse(response);
  },

  delete: async (endpoint: string, options: RequestInit = {}) => {
    const response = await fetch(`${API_BASE_URL}/api${endpoint}`, {
      ...options,
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    return handleResponse(response);
  }
};
