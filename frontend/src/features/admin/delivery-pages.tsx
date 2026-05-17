import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import type { ReactNode } from "react";
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
import type {
  Department,
  Major,
  Offering,
  Professor,
  RegistrationPeriod,
  Room,
  RoomAllocation,
  Section,
  Semester,
} from "../../lib/types";

function EntityTablePage<T extends { id: number }>({
  eyebrow,
  title,
  description,
  rows,
  columns,
  onCreate,
}: {
  eyebrow: string;
  title: string;
  description: string;
  rows: T[];
  columns: Array<{ key: string; label: string; render: (row: T) => ReactNode }>;
  onCreate: () => void;
}) {
  return (
    <>
      <PageHeader eyebrow={eyebrow} title={title} description={description} actions={<button onClick={onCreate}>New</button>} />
      <Panel>
        {rows.length ? <DataTable rows={rows} columns={columns} /> : <EmptyState title={`No ${title.toLowerCase()} yet`} message="Create the first record to get started." />}
      </Panel>
    </>
  );
}

export function SemesterPage() {
  const client = useQueryClient();
  const [editing, setEditing] = useState<Semester | "new" | null>(null);
  const query = useQuery({ queryKey: ["admin", "semesters"], queryFn: adminApi.semesters });
  const mutation = useMutation({
    mutationFn: (payload: { id?: number; body: unknown }) =>
      payload.id ? adminApi.updateSemester(payload.id, payload.body) : adminApi.createSemester(payload.body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["admin", "semesters"] });
      setEditing(null);
    },
  });
  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState message={query.error.message} />;
  return (
    <>
      <EntityTablePage
        eyebrow="Academic setup"
        title="Semesters"
        description="Manage term lifecycle and archive semesters after dependent offerings are retired."
        rows={query.data ?? []}
        onCreate={() => setEditing("new")}
        columns={[
          { key: "name", label: "Name", render: (row) => row.name },
          { key: "status", label: "Status", render: (row) => <Badge>{row.status}</Badge> },
          {
            key: "actions",
            label: "Actions",
            render: (row) => <button className="ghost-button" onClick={() => setEditing(row)}>Edit</button>,
          },
        ]}
      />
      {editing ? (
        <SemesterDrawer
          semester={editing === "new" ? undefined : editing}
          onClose={() => setEditing(null)}
          onSubmit={(body) => mutation.mutate({ id: editing === "new" ? undefined : editing.id, body })}
        />
      ) : null}
    </>
  );
}

function SemesterDrawer({
  semester,
  onClose,
  onSubmit,
}: {
  semester?: Semester;
  onClose: () => void;
  onSubmit: (body: unknown) => void;
}) {
  const { register, handleSubmit } = useForm({
    defaultValues: { name: semester?.name ?? "", status: semester?.status ?? "active" },
  });
  return (
    <Drawer title={semester ? "Edit semester" : "Create semester"} onClose={onClose}>
      <form className="form-grid" onSubmit={handleSubmit(onSubmit)}>
        <label className="span-2">Name<input {...register("name")} /></label>
        <label>Status<select {...register("status")}><option value="draft">draft</option><option value="active">active</option><option value="archived">archived</option></select></label>
        <button>{semester ? "Save changes" : "Create semester"}</button>
      </form>
    </Drawer>
  );
}

export function DepartmentPage() {
  const client = useQueryClient();
  const [editing, setEditing] = useState<Department | "new" | null>(null);
  const query = useQuery({ queryKey: ["admin", "departments"], queryFn: adminApi.departments });
  const mutation = useMutation({
    mutationFn: (payload: { id?: number; body: unknown }) =>
      payload.id ? adminApi.updateDepartment(payload.id, payload.body) : adminApi.createDepartment(payload.body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["admin", "departments"] });
      setEditing(null);
    },
  });
  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState message={query.error.message} />;
  return (
    <>
      <EntityTablePage
        eyebrow="Academic setup"
        title="Departments"
        description="Retire departments only after active majors and courses are archived."
        rows={query.data ?? []}
        onCreate={() => setEditing("new")}
        columns={[
          { key: "code", label: "Code", render: (row) => row.code },
          { key: "name", label: "Name", render: (row) => row.name },
          { key: "state", label: "State", render: (row) => <Badge>{row.is_active ? "active" : "archived"}</Badge> },
          { key: "actions", label: "Actions", render: (row) => <button className="ghost-button" onClick={() => setEditing(row)}>Edit</button> },
        ]}
      />
      {editing ? <DepartmentDrawer department={editing === "new" ? undefined : editing} onClose={() => setEditing(null)} onSubmit={(body) => mutation.mutate({ id: editing === "new" ? undefined : editing.id, body })} /> : null}
    </>
  );
}

function DepartmentDrawer({ department, onClose, onSubmit }: { department?: Department; onClose: () => void; onSubmit: (body: unknown) => void }) {
  const { register, handleSubmit } = useForm({ defaultValues: { code: department?.code ?? "", name: department?.name ?? "", is_active: department?.is_active ?? true } });
  return (
    <Drawer title={department ? "Edit department" : "Create department"} onClose={onClose}>
      <form className="form-grid" onSubmit={handleSubmit(onSubmit)}>
        <label>Code<input {...register("code")} /></label>
        <label>Name<input {...register("name")} /></label>
        {department ? <label className="checkbox-row"><input type="checkbox" {...register("is_active")} /> Active</label> : null}
        <button>{department ? "Save changes" : "Create department"}</button>
      </form>
    </Drawer>
  );
}

export function MajorPage() {
  const client = useQueryClient();
  const [editing, setEditing] = useState<Major | "new" | null>(null);
  const query = useQuery({ queryKey: ["admin", "majors"], queryFn: () => adminApi.majors() });
  const mutation = useMutation({
    mutationFn: (payload: { id?: number; body: unknown }) =>
      payload.id ? adminApi.updateMajor(payload.id, payload.body) : adminApi.createMajor(payload.body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["admin", "majors"] });
      setEditing(null);
    },
  });
  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState message={query.error.message} />;
  return (
    <>
      <EntityTablePage
        eyebrow="Academic setup"
        title="Majors"
        description="Maintain majors while keeping historical student references intact."
        rows={query.data ?? []}
        onCreate={() => setEditing("new")}
        columns={[
          { key: "code", label: "Code", render: (row) => row.code },
          { key: "name", label: "Name", render: (row) => row.name },
          { key: "department", label: "Department ID", render: (row) => row.department_id },
          { key: "state", label: "State", render: (row) => <Badge>{row.is_active ? "active" : "archived"}</Badge> },
          { key: "actions", label: "Actions", render: (row) => <button className="ghost-button" onClick={() => setEditing(row)}>Edit</button> },
        ]}
      />
      {editing ? <MajorDrawer major={editing === "new" ? undefined : editing} onClose={() => setEditing(null)} onSubmit={(body) => mutation.mutate({ id: editing === "new" ? undefined : editing.id, body })} /> : null}
    </>
  );
}

function MajorDrawer({ major, onClose, onSubmit }: { major?: Major; onClose: () => void; onSubmit: (body: unknown) => void }) {
  const { register, handleSubmit } = useForm({ defaultValues: { department_id: major?.department_id ?? "", code: major?.code ?? "", name: major?.name ?? "", is_active: major?.is_active ?? true } });
  return (
    <Drawer title={major ? "Edit major" : "Create major"} onClose={onClose}>
      <form className="form-grid" onSubmit={handleSubmit((values) => onSubmit({ ...values, department_id: Number(values.department_id) }))}>
        <label>Department ID<input {...register("department_id")} /></label>
        <label>Code<input {...register("code")} /></label>
        <label className="span-2">Name<input {...register("name")} /></label>
        {major ? <label className="checkbox-row"><input type="checkbox" {...register("is_active")} /> Active</label> : null}
        <button>{major ? "Save changes" : "Create major"}</button>
      </form>
    </Drawer>
  );
}

export function ProfessorPage() {
  const client = useQueryClient();
  const [editing, setEditing] = useState<Professor | "new" | null>(null);
  const query = useQuery({ queryKey: ["admin", "professors"], queryFn: adminApi.professors });
  const mutation = useMutation({
    mutationFn: (payload: { id?: number; body: unknown }) =>
      payload.id ? adminApi.updateProfessor(payload.id, payload.body) : adminApi.createProfessor(payload.body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["admin", "professors"] });
      setEditing(null);
    },
  });
  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState message={query.error.message} />;
  return (
    <>
      <EntityTablePage
        eyebrow="Delivery"
        title="Professors"
        description="Archive professors only after their active sections are closed."
        rows={query.data ?? []}
        onCreate={() => setEditing("new")}
        columns={[
          { key: "name", label: "Name", render: (row) => row.full_name },
          { key: "email", label: "Email", render: (row) => row.email ?? "—" },
          { key: "state", label: "State", render: (row) => <Badge>{row.is_active ? "active" : "archived"}</Badge> },
          { key: "actions", label: "Actions", render: (row) => <button className="ghost-button" onClick={() => setEditing(row)}>Edit</button> },
        ]}
      />
      {editing ? <ProfessorDrawer professor={editing === "new" ? undefined : editing} onClose={() => setEditing(null)} onSubmit={(body) => mutation.mutate({ id: editing === "new" ? undefined : editing.id, body })} /> : null}
    </>
  );
}

function ProfessorDrawer({ professor, onClose, onSubmit }: { professor?: Professor; onClose: () => void; onSubmit: (body: unknown) => void }) {
  const { register, handleSubmit } = useForm({
    defaultValues: {
      email: professor?.email ?? "",
      full_name: professor?.full_name ?? "",
      department_name: professor?.department_name ?? "",
      password: "",
      is_active: professor?.is_active ?? true,
    },
  });
  return (
    <Drawer title={professor ? "Edit professor" : "Create professor"} onClose={onClose}>
      <form className="form-grid" onSubmit={handleSubmit((values) => {
        const body = professor
          ? { email: values.email, full_name: values.full_name, department_name: values.department_name || null, is_active: values.is_active }
          : { email: values.email, full_name: values.full_name, department_name: values.department_name || null, password: values.password || "prof12345" };
        onSubmit(body);
      })}>
        <label>Email<input {...register("email")} /></label>
        <label>Name<input {...register("full_name")} /></label>
        <label className="span-2">Department<input {...register("department_name")} /></label>
        {!professor ? <label className="span-2">Password<input type="password" {...register("password")} /></label> : null}
        {professor ? <label className="checkbox-row"><input type="checkbox" {...register("is_active")} /> Active</label> : null}
        <button>{professor ? "Save changes" : "Create professor"}</button>
      </form>
    </Drawer>
  );
}

export function RoomPage() {
  const client = useQueryClient();
  const [editing, setEditing] = useState<Room | "new" | null>(null);
  const query = useQuery({ queryKey: ["admin", "rooms"], queryFn: adminApi.rooms });
  const mutation = useMutation({
    mutationFn: (payload: { id?: number; body: unknown }) =>
      payload.id ? adminApi.updateRoom(payload.id, payload.body) : adminApi.createRoom(payload.body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["admin", "rooms"] });
      setEditing(null);
    },
  });
  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState message={query.error.message} />;
  return (
    <>
      <EntityTablePage
        eyebrow="Delivery"
        title="Rooms"
        description="Manage capacity and archive rooms only after active allocations are removed."
        rows={query.data ?? []}
        onCreate={() => setEditing("new")}
        columns={[
          { key: "room", label: "Room", render: (row) => `${row.building ?? "—"} ${row.room_number}` },
          { key: "capacity", label: "Capacity", render: (row) => row.capacity },
          { key: "type", label: "Type", render: (row) => row.room_type },
          { key: "state", label: "State", render: (row) => <Badge>{row.is_active ? "active" : "archived"}</Badge> },
          { key: "actions", label: "Actions", render: (row) => <button className="ghost-button" onClick={() => setEditing(row)}>Edit</button> },
        ]}
      />
      {editing ? <RoomDrawer room={editing === "new" ? undefined : editing} onClose={() => setEditing(null)} onSubmit={(body) => mutation.mutate({ id: editing === "new" ? undefined : editing.id, body })} /> : null}
    </>
  );
}

function RoomDrawer({ room, onClose, onSubmit }: { room?: Room; onClose: () => void; onSubmit: (body: unknown) => void }) {
  const { register, handleSubmit } = useForm({ defaultValues: { building: room?.building ?? "", room_number: room?.room_number ?? "", capacity: room?.capacity ?? 30, room_type: room?.room_type ?? "lecture", is_active: room?.is_active ?? true } });
  return (
    <Drawer title={room ? "Edit room" : "Create room"} onClose={onClose}>
      <form className="form-grid" onSubmit={handleSubmit((values) => onSubmit({ ...values, capacity: Number(values.capacity), building: values.building || null }))}>
        <label>Building<input {...register("building")} /></label>
        <label>Room number<input {...register("room_number")} /></label>
        <label>Capacity<input type="number" {...register("capacity")} /></label>
        <label>Type<input {...register("room_type")} /></label>
        {room ? <label className="checkbox-row"><input type="checkbox" {...register("is_active")} /> Active</label> : null}
        <button>{room ? "Save changes" : "Create room"}</button>
      </form>
    </Drawer>
  );
}

export function OfferingPage() {
  const client = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Offering | null>(null);
  const query = useQuery({ queryKey: ["admin", "offerings"], queryFn: () => adminApi.offerings() });
  const mutation = useMutation({
    mutationFn: (payload: { id?: number; body: unknown }) =>
      payload.id ? adminApi.updateOffering(payload.id, payload.body) : adminApi.createOffering(payload.body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["admin", "offerings"] });
      setCreating(false);
      setEditing(null);
    },
  });
  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState message={query.error.message} />;
  return (
    <>
      <EntityTablePage
        eyebrow="Academic setup"
        title="Offerings"
        description="Archive offerings only after active sections are closed."
        rows={query.data ?? []}
        onCreate={() => setCreating(true)}
        columns={[
          { key: "course", label: "Course", render: (row) => `${row.course_code} · ${row.course_title}` },
          { key: "semester", label: "Semester", render: (row) => row.semester_name },
          { key: "status", label: "Status", render: (row) => <Badge>{row.status}</Badge> },
          { key: "actions", label: "Actions", render: (row) => <button className="ghost-button" onClick={() => setEditing(row)}>Edit</button> },
        ]}
      />
      {creating ? <OfferingDrawer onClose={() => setCreating(false)} onSubmit={(body) => mutation.mutate({ body })} /> : null}
      {editing ? <OfferingDrawer offering={editing} onClose={() => setEditing(null)} onSubmit={(body) => mutation.mutate({ id: editing.id, body })} /> : null}
    </>
  );
}

function OfferingDrawer({ offering, onClose, onSubmit }: { offering?: Offering; onClose: () => void; onSubmit: (body: unknown) => void }) {
  const { register, handleSubmit } = useForm({ defaultValues: { course_id: offering?.course_id ?? "", semester_id: offering?.semester_id ?? "", status: offering?.status ?? "active" } });
  return (
    <Drawer title={offering ? "Edit offering" : "Create offering"} onClose={onClose}>
      <form className="form-grid" onSubmit={handleSubmit((values) => onSubmit(offering ? { status: values.status } : { course_id: Number(values.course_id), semester_id: Number(values.semester_id), status: values.status }))}>
        {!offering ? <label>Course ID<input {...register("course_id")} /></label> : null}
        {!offering ? <label>Semester ID<input {...register("semester_id")} /></label> : null}
        <label>Status<select {...register("status")}><option value="draft">draft</option><option value="active">active</option><option value="cancelled">cancelled</option><option value="archived">archived</option></select></label>
        <button>{offering ? "Save changes" : "Create offering"}</button>
      </form>
    </Drawer>
  );
}

const pageSize = 10;

export function SectionListPage() {
  const client = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Section | null>(null);
  const [courseId, setCourseId] = useState("");
  const [semesterId, setSemesterId] = useState("");
  const [statusValue, setStatusValue] = useState("");
  const [offset, setOffset] = useState(0);
  const params = useMemo(() => {
    const value = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
    if (courseId) value.set("course_id", courseId);
    if (semesterId) value.set("semester_id", semesterId);
    if (statusValue) value.set("status", statusValue);
    return value;
  }, [courseId, offset, semesterId, statusValue]);
  const query = useQuery({ queryKey: ["admin", "sections", params.toString()], queryFn: () => adminApi.sections(params) });
  const mutation = useMutation({
    mutationFn: (payload: { id?: number; body: unknown }) =>
      payload.id ? adminApi.updateSection(payload.id, payload.body) : adminApi.createSection(payload.body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["admin", "sections"] });
      setCreating(false);
      setEditing(null);
    },
  });
  return (
    <>
      <PageHeader eyebrow="Delivery" title="Sections" description="Maintain teaching sections, capacity, and lifecycle state." actions={<button onClick={() => setCreating(true)}>New section</button>} />
      <Panel>
        <div className="filter-row">
          <input placeholder="Course ID" value={courseId} onChange={(event) => { setCourseId(event.target.value); setOffset(0); }} />
          <input placeholder="Semester ID" value={semesterId} onChange={(event) => { setSemesterId(event.target.value); setOffset(0); }} />
          <select value={statusValue} onChange={(event) => { setStatusValue(event.target.value); setOffset(0); }}>
            <option value="">All statuses</option>
            <option value="draft">draft</option>
            <option value="open">open</option>
            <option value="closed">closed</option>
            <option value="cancelled">cancelled</option>
          </select>
        </div>
        {query.isLoading ? <LoadingState /> : null}
        {query.error ? <ErrorState message={query.error.message} /> : null}
        {query.data && query.data.items.length ? (
          <>
            <DataTable<Section>
              rows={query.data.items}
              columns={[
                { key: "section", label: "Section", render: (row) => <Link className="link" to={`/admin/sections/${row.id}`}>{row.course_code} · {row.section_code}</Link> },
                { key: "semester", label: "Semester", render: (row) => row.semester_name },
                { key: "capacity", label: "Capacity", render: (row) => `${row.enrolled_count}/${row.capacity}` },
                { key: "status", label: "Status", render: (row) => <Badge>{row.status}</Badge> },
                { key: "actions", label: "Actions", render: (row) => <button className="ghost-button" onClick={() => setEditing(row)}>Edit</button> },
              ]}
            />
            <Pagination total={query.data.total} limit={query.data.limit} offset={query.data.offset} onChange={setOffset} />
          </>
        ) : query.data ? <EmptyState title="No sections found" message="Adjust the filters or create a section." /> : null}
      </Panel>
      {creating ? <SectionDrawer onClose={() => setCreating(false)} onSubmit={(body) => mutation.mutate({ body })} /> : null}
      {editing ? <SectionDrawer section={editing} onClose={() => setEditing(null)} onSubmit={(body) => mutation.mutate({ id: editing.id, body })} /> : null}
    </>
  );
}

function SectionDrawer({ section, onClose, onSubmit }: { section?: Section; onClose: () => void; onSubmit: (body: unknown) => void }) {
  const { register, handleSubmit } = useForm({
    defaultValues: {
      course_offering_id: section?.course_offering_id ?? "",
      professor_id: section?.professor_id ?? "",
      section_code: section?.section_code ?? "",
      capacity: section?.capacity ?? 30,
      room_selection_mode: section?.room_selection_mode ?? "admin_fixed",
      status: section?.status ?? "open",
    },
  });
  return (
    <Drawer title={section ? "Edit section" : "Create section"} onClose={onClose}>
      <form className="form-grid" onSubmit={handleSubmit((values) => onSubmit(section ? {
        professor_id: values.professor_id ? Number(values.professor_id) : null,
        section_code: values.section_code,
        capacity: Number(values.capacity),
        room_selection_mode: values.room_selection_mode,
        status: values.status,
      } : {
        course_offering_id: Number(values.course_offering_id),
        professor_id: values.professor_id ? Number(values.professor_id) : null,
        section_code: values.section_code,
        capacity: Number(values.capacity),
        room_selection_mode: values.room_selection_mode,
        status: values.status,
      }))}>
        {!section ? <label>Offering ID<input {...register("course_offering_id")} /></label> : null}
        <label>Professor ID<input {...register("professor_id")} /></label>
        <label>Section code<input {...register("section_code")} /></label>
        <label>Capacity<input type="number" {...register("capacity")} /></label>
        <label>Room mode<select {...register("room_selection_mode")}><option value="admin_fixed">admin_fixed</option><option value="professor_choice">professor_choice</option><option value="system_recommended">system_recommended</option></select></label>
        <label>Status<select {...register("status")}><option value="draft">draft</option><option value="open">open</option><option value="closed">closed</option><option value="cancelled">cancelled</option></select></label>
        <button>{section ? "Save changes" : "Create section"}</button>
      </form>
    </Drawer>
  );
}

export function SectionDetailPage() {
  const { sectionId } = useParams();
  const id = Number(sectionId);
  const query = useQuery({ queryKey: ["admin", "section", id], queryFn: () => adminApi.section(id) });
  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState message={query.error.message} />;
  const section = query.data!;
  return (
    <>
      <PageHeader eyebrow="Section" title={`${section.course_code} · ${section.section_code}`} description={`${section.semester_name} · ${section.enrolled_count}/${section.capacity} enrolled`} actions={<Link className="button" to={`/admin/sections/${id}/rooms`}>Manage rooms</Link>} />
      <Panel>
        <dl className="detail-list">
          <div><dt>Status</dt><dd>{section.status}</dd></div>
          <div><dt>Remaining seats</dt><dd>{section.remaining_seats}</dd></div>
          <div><dt>Waitlist</dt><dd>{section.waitlist_count}</dd></div>
          <div><dt>Room mode</dt><dd>{section.room_selection_mode}</dd></div>
        </dl>
      </Panel>
    </>
  );
}

export function SectionRoomsPage() {
  const { sectionId } = useParams();
  const id = Number(sectionId);
  const client = useQueryClient();
  const [adding, setAdding] = useState(false);
  const allocations = useQuery({ queryKey: ["admin", "section", id, "rooms"], queryFn: () => adminApi.roomAllocations(id) });
  const rooms = useQuery({ queryKey: ["admin", "rooms"], queryFn: adminApi.rooms });
  const createMutation = useMutation({
    mutationFn: (body: unknown) => adminApi.allocateRooms(id, body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["admin", "section", id, "rooms"] });
      setAdding(false);
    },
  });
  const deleteMutation = useMutation({
    mutationFn: (roomId: number) => adminApi.removeRoomAllocation(id, roomId),
    onSuccess: () => client.invalidateQueries({ queryKey: ["admin", "section", id, "rooms"] }),
  });
  if (allocations.isLoading || rooms.isLoading) return <LoadingState />;
  if (allocations.error) return <ErrorState message={allocations.error.message} />;
  return (
    <>
      <PageHeader eyebrow="Section" title="Room allocations" description="Remove only rooms that are not currently selected by the professor." actions={<button onClick={() => setAdding(true)}>Add rooms</button>} />
      <Panel>
        {allocations.data?.length ? (
          <DataTable<RoomAllocation>
            rows={allocations.data}
            columns={[
              { key: "room", label: "Room", render: (row) => `${row.building ?? "—"} ${row.room_number}` },
              { key: "capacity", label: "Capacity", render: (row) => row.capacity },
              { key: "type", label: "Type", render: (row) => row.room_type },
              { key: "actions", label: "Actions", render: (row) => <button className="danger-button" onClick={() => deleteMutation.mutate(row.room_id)}>Remove</button> },
            ]}
          />
        ) : <EmptyState title="No room allocations" message="Add allowed rooms for this section." />}
      </Panel>
      {adding ? <RoomAllocationDrawer rooms={rooms.data ?? []} onClose={() => setAdding(false)} onSubmit={(body) => createMutation.mutate(body)} /> : null}
    </>
  );
}

function RoomAllocationDrawer({ rooms, onClose, onSubmit }: { rooms: Room[]; onClose: () => void; onSubmit: (body: unknown) => void }) {
  const { register, handleSubmit } = useForm({ defaultValues: { room_ids: "", notes: "" } });
  return (
    <Drawer title="Add room allocations" onClose={onClose}>
      <p className="muted">Available room IDs: {rooms.map((room) => `${room.id}=${room.room_number}`).join(", ")}</p>
      <form className="form-grid" onSubmit={handleSubmit((values) => onSubmit({ room_ids: values.room_ids.split(",").map((value) => Number(value.trim())).filter(Boolean), notes: values.notes || null }))}>
        <label className="span-2">Room IDs<input {...register("room_ids")} /></label>
        <label className="span-2">Notes<textarea {...register("notes")} /></label>
        <button>Add rooms</button>
      </form>
    </Drawer>
  );
}

export function RegistrationPeriodPage() {
  const client = useQueryClient();
  const [editing, setEditing] = useState<RegistrationPeriod | "new" | null>(null);
  const query = useQuery({ queryKey: ["admin", "registration-periods"], queryFn: () => adminApi.registrationPeriods() });
  const mutation = useMutation({
    mutationFn: (payload: { id?: number; body: unknown }) =>
      payload.id ? adminApi.updateRegistrationPeriod(payload.id, payload.body) : adminApi.createRegistrationPeriod(payload.body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["admin", "registration-periods"] });
      setEditing(null);
    },
  });
  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState message={query.error.message} />;
  return (
    <>
      <EntityTablePage
        eyebrow="Delivery"
        title="Registration periods"
        description="Manage open and closed windows without overlapping periods."
        rows={query.data ?? []}
        onCreate={() => setEditing("new")}
        columns={[
          { key: "semester", label: "Semester", render: (row) => row.semester_name },
          { key: "opens", label: "Opens", render: (row) => new Date(row.opens_at).toLocaleString() },
          { key: "closes", label: "Closes", render: (row) => new Date(row.closes_at).toLocaleString() },
          { key: "status", label: "Status", render: (row) => <Badge>{row.status}</Badge> },
          { key: "actions", label: "Actions", render: (row) => <button className="ghost-button" onClick={() => setEditing(row)}>Edit</button> },
        ]}
      />
      {editing ? <RegistrationPeriodDrawer period={editing === "new" ? undefined : editing} onClose={() => setEditing(null)} onSubmit={(body) => mutation.mutate({ id: editing === "new" ? undefined : editing.id, body })} /> : null}
    </>
  );
}

function RegistrationPeriodDrawer({ period, onClose, onSubmit }: { period?: RegistrationPeriod; onClose: () => void; onSubmit: (body: unknown) => void }) {
  const localValue = (value?: string) => value ? new Date(value).toISOString().slice(0, 16) : "";
  const { register, handleSubmit } = useForm({ defaultValues: { semester_id: period?.semester_id ?? "", opens_at: localValue(period?.opens_at), closes_at: localValue(period?.closes_at), status: period?.status ?? "open" } });
  return (
    <Drawer title={period ? "Edit period" : "Create period"} onClose={onClose}>
      <form className="form-grid" onSubmit={handleSubmit((values) => onSubmit(period ? {
        opens_at: new Date(values.opens_at).toISOString(),
        closes_at: new Date(values.closes_at).toISOString(),
        status: values.status,
      } : {
        semester_id: Number(values.semester_id),
        opens_at: new Date(values.opens_at).toISOString(),
        closes_at: new Date(values.closes_at).toISOString(),
        status: values.status,
      }))}>
        {!period ? <label>Semester ID<input {...register("semester_id")} /></label> : null}
        <label>Opens<input type="datetime-local" {...register("opens_at")} /></label>
        <label>Closes<input type="datetime-local" {...register("closes_at")} /></label>
        <label>Status<select {...register("status")}><option value="open">open</option><option value="closed">closed</option></select></label>
        <button>{period ? "Save changes" : "Create period"}</button>
      </form>
    </Drawer>
  );
}
