import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";

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
import type { CourseDetail, CourseSummary, EligibilityRule } from "../../lib/types";

const pageSize = 10;

export function CourseListPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [active, setActive] = useState<string>("");
  const [offset, setOffset] = useState(0);
  const params = useMemo(() => {
    const value = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
    if (search) value.set("search", search);
    if (departmentId) value.set("department_id", departmentId);
    if (active) value.set("is_active", active);
    return value;
  }, [active, departmentId, offset, search]);
  const query = useQuery({ queryKey: ["admin", "courses", params.toString()], queryFn: () => adminApi.courses(params) });

  return (
    <>
      <PageHeader
        eyebrow="Academic setup"
        title="Courses"
        description="Manage the catalog, archive retired records, and open each course for rules and prerequisites."
        actions={<button onClick={() => navigate("/admin/courses/new")}>New course</button>}
      />
      <Panel>
        <div className="filter-row">
          <input placeholder="Search code or title" value={search} onChange={(event) => { setSearch(event.target.value); setOffset(0); }} />
          <input placeholder="Department ID" value={departmentId} onChange={(event) => { setDepartmentId(event.target.value); setOffset(0); }} />
          <select value={active} onChange={(event) => { setActive(event.target.value); setOffset(0); }}>
            <option value="">All states</option>
            <option value="true">Active</option>
            <option value="false">Archived</option>
          </select>
        </div>
        {query.isLoading ? <LoadingState /> : null}
        {query.error ? <ErrorState message={query.error.message} /> : null}
        {query.data && query.data.items.length === 0 ? (
          <EmptyState title="No courses yet" message="Create the first course to begin catalog setup." />
        ) : null}
        {query.data && query.data.items.length ? (
          <>
            <DataTable<CourseSummary>
              rows={query.data.items}
              columns={[
                {
                  key: "course",
                  label: "Course",
                  render: (course) => (
                    <Link className="link" to={`/admin/courses/${course.id}`}>
                      {course.code} · {course.title}
                    </Link>
                  ),
                },
                { key: "department", label: "Department", render: (course) => course.department_code ?? "—" },
                { key: "credits", label: "Credits", render: (course) => course.credits },
                {
                  key: "status",
                  label: "State",
                  render: (course) => <Badge tone={course.is_active ? "success" : "muted"}>{course.is_active ? "Active" : "Archived"}</Badge>,
                },
                {
                  key: "counts",
                  label: "Usage",
                  render: (course) => `${course.active_offering_count} offerings · ${course.active_section_count} sections`,
                },
              ]}
            />
            <Pagination total={query.data.total} limit={query.data.limit} offset={query.data.offset} onChange={setOffset} />
          </>
        ) : null}
      </Panel>
    </>
  );
}

type CourseFormValues = {
  department_id: string;
  code: string;
  title: string;
  credits: number;
  description: string;
  course_type: string;
  is_repeatable: boolean;
};

function CourseForm({
  initial,
  onSubmit,
  submitLabel,
}: {
  initial?: CourseDetail;
  onSubmit: (values: Record<string, unknown>) => void;
  submitLabel: string;
}) {
  const { register, handleSubmit } = useForm<CourseFormValues>({
    defaultValues: {
      department_id: initial?.department_id?.toString() ?? "",
      code: initial?.code ?? "",
      title: initial?.title ?? "",
      credits: initial?.credits ?? 3,
      description: initial?.description ?? "",
      course_type: initial?.course_type ?? "",
      is_repeatable: initial?.is_repeatable ?? false,
    },
  });

  return (
    <form className="form-grid" onSubmit={handleSubmit((values) => onSubmit({
      department_id: values.department_id ? Number(values.department_id) : null,
      code: values.code,
      title: values.title,
      credits: Number(values.credits),
      description: values.description || null,
      course_type: values.course_type || null,
      is_repeatable: values.is_repeatable,
    }))}>
      <label>Department ID<input {...register("department_id")} /></label>
      <label>Code<input {...register("code", { required: true })} /></label>
      <label>Title<input {...register("title", { required: true })} /></label>
      <label>Credits<input type="number" {...register("credits", { valueAsNumber: true })} /></label>
      <label>Course type<input {...register("course_type")} /></label>
      <label className="checkbox-row"><input type="checkbox" {...register("is_repeatable")} /> Repeatable</label>
      <label className="span-2">Description<textarea {...register("description")} /></label>
      <button type="submit">{submitLabel}</button>
    </form>
  );
}

export function NewCoursePage() {
  const navigate = useNavigate();
  const mutation = useMutation({
    mutationFn: adminApi.createCourse,
    onSuccess: (course) => navigate(`/admin/courses/${course.id}`),
  });
  return (
    <>
      <PageHeader eyebrow="Academic setup" title="Create course" description="Add a course before defining its prerequisites and rules." />
      <Panel>
        <CourseForm onSubmit={(values) => mutation.mutate(values)} submitLabel="Create course" />
        {mutation.error ? <p className="error-copy">{mutation.error.message}</p> : null}
      </Panel>
    </>
  );
}

export function CourseDetailPage() {
  const { courseId } = useParams();
  const id = Number(courseId);
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const courseQuery = useQuery({ queryKey: ["admin", "course", id], queryFn: () => adminApi.course(id) });
  const updateMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => adminApi.updateCourse(id, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "course", id] });
      queryClient.invalidateQueries({ queryKey: ["admin", "courses"] });
      setEditing(false);
    },
  });
  const archiveMutation = useMutation({
    mutationFn: () => adminApi.updateCourse(id, { is_active: false }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "course", id] }),
  });
  const restoreMutation = useMutation({
    mutationFn: () => adminApi.updateCourse(id, { is_active: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "course", id] });
      queryClient.invalidateQueries({ queryKey: ["admin", "courses"] });
    },
  });

  if (courseQuery.isLoading) return <LoadingState />;
  if (courseQuery.error) return <ErrorState message={courseQuery.error.message} />;
  const course = courseQuery.data!;
  return (
    <>
      <PageHeader
        eyebrow="Course"
        title={`${course.code} · ${course.title}`}
        description={course.description ?? "No description provided."}
        actions={
          <div className="button-cluster">
            <button className="ghost-button" onClick={() => setEditing(true)}>Edit</button>
            {course.is_active ? (
              <button className="danger-button" onClick={() => archiveMutation.mutate()}>Archive</button>
            ) : (
              <button onClick={() => restoreMutation.mutate()}>Restore</button>
            )}
          </div>
        }
      />
      <section className="detail-grid">
        <Panel>
          <h3>Overview</h3>
          <dl className="detail-list">
            <div><dt>Department</dt><dd>{course.department_name ?? "—"}</dd></div>
            <div><dt>Credits</dt><dd>{course.credits}</dd></div>
            <div><dt>Type</dt><dd>{course.course_type ?? "—"}</dd></div>
            <div><dt>Status</dt><dd>{course.is_active ? "Active" : "Archived"}</dd></div>
          </dl>
        </Panel>
        <Panel>
          <h3>Rules</h3>
          <div className="button-cluster">
            <Link className="ghost-button" to={`/admin/courses/${id}/prerequisites`}>Prerequisites</Link>
            <Link className="ghost-button" to={`/admin/courses/${id}/eligibility-rules`}>Eligibility rules</Link>
          </div>
        </Panel>
      </section>
      {editing ? (
        <Drawer title="Edit course" onClose={() => setEditing(false)}>
          <CourseForm initial={course} onSubmit={(values) => updateMutation.mutate(values)} submitLabel="Save changes" />
          {updateMutation.error ? <p className="error-copy">{updateMutation.error.message}</p> : null}
        </Drawer>
      ) : null}
    </>
  );
}

export function CoursePrerequisitesPage() {
  const { courseId } = useParams();
  const id = Number(courseId);
  const queryClient = useQueryClient();
  const courseQuery = useQuery({ queryKey: ["admin", "course", id], queryFn: () => adminApi.course(id) });
  const allCoursesQuery = useQuery({
    queryKey: ["admin", "courses", "all-active"],
    queryFn: () => adminApi.courses(new URLSearchParams({ limit: "100", offset: "0", is_active: "true" })),
  });
  const { register, handleSubmit, reset } = useForm<{ ids: string }>({ defaultValues: { ids: "" } });
  const mutation = useMutation({
    mutationFn: (ids: number[]) => adminApi.replacePrerequisites(id, { prerequisite_course_ids: ids, rule_group: "all" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "course", id] });
      reset();
    },
  });
  if (courseQuery.isLoading || allCoursesQuery.isLoading) return <LoadingState />;
  if (courseQuery.error) return <ErrorState message={courseQuery.error.message} />;
  return (
    <>
      <PageHeader eyebrow="Course" title="Prerequisites" description={`Replace the full prerequisite set for ${courseQuery.data!.code}.`} />
      <Panel>
        <p className="muted">Available course IDs: {allCoursesQuery.data?.items.map((course) => `${course.id}=${course.code}`).join(", ")}</p>
        <form className="form-grid" onSubmit={handleSubmit((values) => mutation.mutate(
          values.ids.split(",").map((value) => value.trim()).filter(Boolean).map(Number),
        ))}>
          <label className="span-2">Prerequisite course IDs<input {...register("ids")} placeholder="1, 2, 3" /></label>
          <button>Replace prerequisites</button>
        </form>
        <div className="chip-row">
          {courseQuery.data!.prerequisites.map((course) => <Badge key={course.id}>{course.code}</Badge>)}
        </div>
      </Panel>
    </>
  );
}

type RuleFormValues = {
  min_academic_year: string;
  min_gpa: string;
  allowed_department_ids: string;
  allowed_major_ids: string;
};

function rulePayload(values: RuleFormValues) {
  const csv = (value: string) => value.split(",").map((item) => item.trim()).filter(Boolean).map(Number);
  return {
    min_academic_year: values.min_academic_year ? Number(values.min_academic_year) : null,
    min_gpa: values.min_gpa ? Number(values.min_gpa) : null,
    allowed_department_ids: values.allowed_department_ids ? csv(values.allowed_department_ids) : null,
    allowed_major_ids: values.allowed_major_ids ? csv(values.allowed_major_ids) : null,
    rule_metadata: null,
  };
}

function RuleForm({
  rule,
  onSubmit,
  submitLabel,
}: {
  rule?: EligibilityRule;
  onSubmit: (payload: ReturnType<typeof rulePayload>) => void;
  submitLabel: string;
}) {
  const { register, handleSubmit } = useForm<RuleFormValues>({
    defaultValues: {
      min_academic_year: rule?.min_academic_year?.toString() ?? "",
      min_gpa: rule?.min_gpa?.toString() ?? "",
      allowed_department_ids: rule?.allowed_department_ids?.join(", ") ?? "",
      allowed_major_ids: rule?.allowed_major_ids?.join(", ") ?? "",
    },
  });
  return (
    <form className="form-grid" onSubmit={handleSubmit((values) => onSubmit(rulePayload(values)))}>
      <label>Minimum year<input {...register("min_academic_year")} /></label>
      <label>Minimum GPA<input {...register("min_gpa")} /></label>
      <label className="span-2">Allowed departments<input {...register("allowed_department_ids")} /></label>
      <label className="span-2">Allowed majors<input {...register("allowed_major_ids")} /></label>
      <button>{submitLabel}</button>
    </form>
  );
}

export function CourseEligibilityRulesPage() {
  const { courseId } = useParams();
  const id = Number(courseId);
  const queryClient = useQueryClient();
  const [editingRule, setEditingRule] = useState<EligibilityRule | null>(null);
  const [creating, setCreating] = useState(false);
  const courseQuery = useQuery({ queryKey: ["admin", "course", id], queryFn: () => adminApi.course(id) });
  const rulesQuery = useQuery({ queryKey: ["admin", "course", id, "rules"], queryFn: () => adminApi.eligibilityRules(id) });
  const createMutation = useMutation({
    mutationFn: (payload: ReturnType<typeof rulePayload>) => adminApi.createEligibilityRule(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "course", id, "rules"] });
      setCreating(false);
    },
  });
  const updateMutation = useMutation({
    mutationFn: ({ ruleId, payload }: { ruleId: number; payload: ReturnType<typeof rulePayload> }) =>
      adminApi.updateEligibilityRule(id, ruleId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "course", id, "rules"] });
      setEditingRule(null);
    },
  });
  const deleteMutation = useMutation({
    mutationFn: (ruleId: number) => adminApi.deleteEligibilityRule(id, ruleId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "course", id, "rules"] }),
  });
  if (courseQuery.isLoading || rulesQuery.isLoading) return <LoadingState />;
  if (courseQuery.error) return <ErrorState message={courseQuery.error.message} />;
  return (
    <>
      <PageHeader
        eyebrow="Course"
        title="Eligibility rules"
        description={`Manage the eligibility constraints for ${courseQuery.data!.code}.`}
        actions={<button onClick={() => setCreating(true)}>New rule</button>}
      />
      <Panel>
        {rulesQuery.data?.length ? (
          <DataTable<EligibilityRule>
            rows={rulesQuery.data}
            columns={[
              { key: "year", label: "Min year", render: (rule) => rule.min_academic_year ?? "—" },
              { key: "gpa", label: "Min GPA", render: (rule) => rule.min_gpa ?? "—" },
              { key: "departments", label: "Departments", render: (rule) => rule.allowed_department_ids?.join(", ") ?? "Any" },
              { key: "majors", label: "Majors", render: (rule) => rule.allowed_major_ids?.join(", ") ?? "Any" },
              {
                key: "actions",
                label: "Actions",
                render: (rule) => (
                  <div className="button-cluster">
                    <button className="ghost-button" onClick={() => setEditingRule(rule)}>Edit</button>
                    <button className="danger-button" onClick={() => deleteMutation.mutate(rule.id)}>Delete</button>
                  </div>
                ),
              },
            ]}
          />
        ) : (
          <EmptyState title="No rules yet" message="Create a rule when a course needs extra restrictions." />
        )}
      </Panel>
      {creating ? (
        <Drawer title="Create eligibility rule" onClose={() => setCreating(false)}>
          <RuleForm onSubmit={(payload) => createMutation.mutate(payload)} submitLabel="Create rule" />
        </Drawer>
      ) : null}
      {editingRule ? (
        <Drawer title="Edit eligibility rule" onClose={() => setEditingRule(null)}>
          <RuleForm
            rule={editingRule}
            onSubmit={(payload) => updateMutation.mutate({ ruleId: editingRule.id, payload })}
            submitLabel="Save changes"
          />
        </Drawer>
      ) : null}
    </>
  );
}
