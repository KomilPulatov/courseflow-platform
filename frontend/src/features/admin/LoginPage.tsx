import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useLocation, useNavigate } from "react-router-dom";

import { adminApi, authStore } from "../../lib/api";

type LoginValues = { email: string; password: string };

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { register, handleSubmit } = useForm<LoginValues>({
    defaultValues: { email: "admin@crsp.example.com", password: "admin12345" },
  });
  const mutation = useMutation({
    mutationFn: adminApi.login,
    onSuccess: (result) => {
      authStore.admin.set(result.access_token);
      const from = (location.state as { from?: string } | null)?.from ?? "/admin";
      navigate(from, { replace: true });
    },
  });

  return (
    <main className="login-shell">
      <section className="login-card">
        <div className="login-story">
          <div>
            <div className="brand-mark">CR</div>
            <p className="eyebrow">CRSP Administration</p>
            <h1>Shape the academic term with confidence.</h1>
            <p className="muted">
              Manage catalog structure, teaching capacity, scheduling, and system health from one calm workspace.
            </p>
          </div>
        </div>
        <form className="login-form" onSubmit={handleSubmit((values) => mutation.mutate(values))}>
          <label>
            Email
            <input type="email" {...register("email", { required: true })} />
          </label>
          <label>
            Password
            <input type="password" {...register("password", { required: true })} />
          </label>
          {mutation.error ? <p className="error-copy">{mutation.error.message}</p> : null}
          <button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}
