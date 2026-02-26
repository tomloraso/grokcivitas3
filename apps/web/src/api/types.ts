export type HealthResponse = {
  status: string;
};

export type Task = {
  id: string;
  title: string;
  created_at: string;
};

export type CreateTaskRequest = {
  title: string;
};
