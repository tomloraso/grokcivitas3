import { useEffect, useState } from "react";

import { createTask, getHealth, listTasks } from "./api/client";
import type { Task } from "./api/types";

export function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [title, setTitle] = useState("");
  const [health, setHealth] = useState("unknown");

  useEffect(() => {
    void refreshTasks();
    void checkHealth();
  }, []);

  async function refreshTasks(): Promise<void> {
    setTasks(await listTasks());
  }

  async function checkHealth(): Promise<void> {
    const status = await getHealth();
    setHealth(status.status);
  }

  async function onSubmit(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    if (!title.trim()) {
      return;
    }
    await createTask({ title: title.trim() });
    setTitle("");
    await refreshTasks();
  }

  return (
    <main className="container">
      <h1>Civitas</h1>
      <p>Backend health: {health}</p>

      <form onSubmit={onSubmit} className="task-form">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Add task"
          aria-label="Task title"
        />
        <button type="submit">Create</button>
      </form>

      <ul>
        {tasks.map((task) => (
          <li key={task.id}>{task.title}</li>
        ))}
      </ul>
    </main>
  );
}

