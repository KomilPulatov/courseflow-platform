import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router-dom";

import {
  Badge,
  DataTable,
  Drawer,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  Pagination,
  Panel,
} from "../../components/ui";
import { adminApi } from "../../lib/api";
import type { AuditLog, SuggestionRun } from "../../lib/types";

export function DashboardPage() {
  const courses = useQuery({
    queryKey: ["admin", "courses", "dashboard"],
    queryFn: () => adminApi.courses(new URLSearchParams({ limit: "1", offset: "0" })),
  });
  const sections = useQuery({
    queryKey: ["admin", "sections", "dashboard"],
    queryFn: () => adminApi.sections(new URLSearchParams({ limit: "1", offset: "0" })),
  });
  const health = useQuery({ queryKey: ["admin", "dependency-health"], queryFn: adminApi.dependencyHealth });
  const audits = useQuery({
    queryKey: ["admin", "audit", "recent"],
    queryFn: () => adminApi.auditLogs(new URLSearchParams({ limit: "5", offset: "0" })),
  });
  return (
    <>
      <PageHeader eyebrow="Overview" title="Dashboard" description="A quick read on academic setup, delivery, and platform health." />
      <section className="metric-grid">
        <Panel><p className="eyebrow">Courses</p><h3>{courses.data?.total ?? "—"}</h3></Panel>
        <Panel><p className="eyebrow">Sections</p><h3>{sections.data?.total ?? "—"}</h3></Panel>
        <Panel><p className="eyebrow">Health</p><h3>{health.data?.status ?? "—"}</h3></Panel>
      </section>
      <section className="detail-grid">
        <Panel>
          <h3>Quick actions</h3>
          <div className="button-cluster">
            <Link className="button" to="/admin/courses/new">Create course</Link>
            <Link className="ghost-button" to="/admin/sections">Sections</Link>
            <Link className="ghost-button" to="/admin/scheduling">Scheduling</Link>
          </div>
        </Panel>
        <Panel>
          <h3>Recent audit activity</h3>
          {audits.data?.items.length ? (
            <ul className="simple-list">
              {audits.data.items.map((item) => (
                <li key={item.id}>{item.event_type} · {item.entity_type}</li>
              ))}
            </ul>
          ) : <p className="muted">No recent activity.</p>}
        </Panel>
      </section>
    </>
  );
}

const pageSize = 10;

export function SchedulingPage() {
  const client = useQueryClient();
  const [semesterId, setSemesterId] = useState("");
  const [statusValue, setStatusValue] = useState("");
  const [offset, setOffset] = useState(0);
  const [creating, setCreating] = useState(false);
  const params = useMemo(() => {
    const value = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
    if (semesterId) value.set("semester_id", semesterId);
    if (statusValue) value.set("status", statusValue);
    return value;
  }, [offset, semesterId, statusValue]);
  const query = useQuery({ queryKey: ["admin", "scheduling", params.toString()], queryFn: () => adminApi.schedulingRuns(params) });
  const createMutation = useMutation({
    mutationFn: adminApi.createSchedulingRun,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["admin", "scheduling"] });
      setCreating(false);
    },
  });
  return (
    <>
      <PageHeader eyebrow="Delivery" title="Scheduling" description="Review recent suggestion runs with enriched semester context." actions={<button onClick={() => setCreating(true)}>New run</button>} />
      <Panel>
        <div className="filter-row">
          <input placeholder="Semester ID" value={semesterId} onChange={(event) => { setSemesterId(event.target.value); setOffset(0); }} />
          <select value={statusValue} onChange={(event) => { setStatusValue(event.target.value); setOffset(0); }}>
            <option value="">All statuses</option>
            <option value="queued">queued</option>
            <option value="running">running</option>
            <option value="completed">completed</option>
            <option value="approved">approved</option>
            <option value="failed">failed</option>
          </select>
        </div>
        {query.isLoading ? <LoadingState /> : null}
        {query.error ? <ErrorState message={query.error.message} /> : null}
        {query.data?.items.length ? (
          <>
            <DataTable<SuggestionRun>
              rows={query.data.items}
              columns={[
                { key: "id", label: "Run", render: (row) => <Link className="link" to={`/admin/scheduling/${row.id}`}>#{row.id}</Link> },
                { key: "semester", label: "Semester", render: (row) => row.semester_name },
                { key: "strategy", label: "Strategy", render: (row) => row.strategy },
                { key: "status", label: "Status", render: (row) => <Badge>{row.status}</Badge> },
              ]}
            />
            <Pagination total={query.data.total} limit={query.data.limit} offset={query.data.offset} onChange={setOffset} />
          </>
        ) : query.data ? <EmptyState title="No suggestion runs" message="Start a scheduling run to generate options." /> : null}
      </Panel>
      {creating ? <SchedulingDrawer onClose={() => setCreating(false)} onSubmit={(body) => createMutation.mutate(body)} /> : null}
    </>
  );
}

function SchedulingDrawer({ onClose, onSubmit }: { onClose: () => void; onSubmit: (body: { semester_id: number; strategy: string }) => void }) {
  const { register, handleSubmit } = useForm({ defaultValues: { semester_id: "", strategy: "balanced_heuristic" } });
  return (
    <Drawer title="Create suggestion run" onClose={onClose}>
      <form className="form-grid" onSubmit={handleSubmit((values) => onSubmit({ semester_id: Number(values.semester_id), strategy: values.strategy }))}>
        <label>Semester ID<input {...register("semester_id")} /></label>
        <label>Strategy<input {...register("strategy")} /></label>
        <button>Create run</button>
      </form>
    </Drawer>
  );
}

export function SchedulingRunPage() {
  const { runId } = useParams();
  const id = Number(runId);
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["admin", "scheduling", id], queryFn: () => adminApi.schedulingRun(id) });
  const approve = useMutation({
    mutationFn: () => adminApi.approveSchedulingRun(id),
    onSuccess: () => client.invalidateQueries({ queryKey: ["admin", "scheduling", id] }),
  });
  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState message={query.error.message} />;
  return (
    <>
      <PageHeader eyebrow="Scheduling run" title={`Run #${id}`} description={`Status: ${query.data!.status}`} actions={<button onClick={() => approve.mutate()}>Approve run</button>} />
      <Panel>
        {query.data!.items.length ? (
          <DataTable
            rows={query.data!.items}
            columns={[
              { key: "section", label: "Section", render: (row) => row.section_id },
              { key: "room", label: "Room", render: (row) => row.room_id ?? "—" },
              { key: "score", label: "Score", render: (row) => row.score },
              { key: "status", label: "Status", render: (row) => row.status },
            ]}
          />
        ) : <EmptyState title="No suggestion items" message="This run has not produced items yet." />}
      </Panel>
    </>
  );
}

export function AuditLogsPage() {
  const [eventType, setEventType] = useState("");
  const [entityType, setEntityType] = useState("");
  const [createdFrom, setCreatedFrom] = useState("");
  const [createdTo, setCreatedTo] = useState("");
  const [offset, setOffset] = useState(0);
  const params = useMemo(() => {
    const value = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
    if (eventType) value.set("event_type", eventType);
    if (entityType) value.set("entity_type", entityType);
    if (createdFrom) value.set("created_from", new Date(createdFrom).toISOString());
    if (createdTo) value.set("created_to", new Date(createdTo).toISOString());
    return value;
  }, [createdFrom, createdTo, entityType, eventType, offset]);
  const query = useQuery({ queryKey: ["admin", "audit", params.toString()], queryFn: () => adminApi.auditLogs(params) });
  return (
    <>
      <PageHeader eyebrow="Observability" title="Audit logs" description="Filter audit history server-side instead of searching only in the browser." />
      <Panel>
        <div className="filter-row">
          <input placeholder="Event type" value={eventType} onChange={(event) => { setEventType(event.target.value); setOffset(0); }} />
          <input placeholder="Entity type" value={entityType} onChange={(event) => { setEntityType(event.target.value); setOffset(0); }} />
          <input type="datetime-local" value={createdFrom} onChange={(event) => { setCreatedFrom(event.target.value); setOffset(0); }} />
          <input type="datetime-local" value={createdTo} onChange={(event) => { setCreatedTo(event.target.value); setOffset(0); }} />
        </div>
        {query.isLoading ? <LoadingState /> : null}
        {query.error ? <ErrorState message={query.error.message} /> : null}
        {query.data?.items.length ? (
          <>
            <DataTable<AuditLog>
              rows={query.data.items}
              columns={[
                { key: "time", label: "Time", render: (row) => new Date(row.created_at).toLocaleString() },
                { key: "event", label: "Event", render: (row) => row.event_type },
                { key: "entity", label: "Entity", render: (row) => `${row.entity_type} #${row.entity_id ?? "—"}` },
              ]}
            />
            <Pagination total={query.data.total} limit={query.data.limit} offset={query.data.offset} onChange={setOffset} />
          </>
        ) : query.data ? <EmptyState title="No audit logs found" message="Try broader filters." /> : null}
      </Panel>
    </>
  );
}

export function ObservabilityPage() {
  const health = useQuery({ queryKey: ["health"], queryFn: adminApi.health });
  const dependencies = useQuery({ queryKey: ["dependency-health"], queryFn: adminApi.dependencyHealth });
  const metrics = useQuery({ queryKey: ["metrics"], queryFn: adminApi.metrics });
  return (
    <>
      <PageHeader eyebrow="Observability" title="Platform health" description="A concise operations summary for the current stack." />
      <section className="detail-grid">
        <Panel>
          <h3>API health</h3>
          <pre>{JSON.stringify(health.data ?? {}, null, 2)}</pre>
        </Panel>
        <Panel>
          <h3>Dependencies</h3>
          <pre>{JSON.stringify(dependencies.data ?? {}, null, 2)}</pre>
        </Panel>
      </section>
      <Panel>
        <h3>Metrics preview</h3>
        <pre className="metrics-preview">{metrics.data?.slice(0, 1200) ?? ""}</pre>
      </Panel>
    </>
  );
}
