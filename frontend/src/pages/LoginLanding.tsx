import { Link } from "react-router-dom";

type LoginCard = {
  title: string;
  description: string;
  href: string;
};

const cards: LoginCard[] = [
  {
    title: "Student",
    description: "Sign in to register for courses and manage your schedule.",
    href: "/login/student",
  },
  {
    title: "Professor",
    description: "Review assigned sections and manage availability.",
    href: "/login/professor",
  },
  {
    title: "Administrator",
    description: "Manage semesters, courses, rooms, and scheduling runs.",
    href: "/login/admin",
  },
];

export default function LoginLanding() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-900">CourseFlow</h1>
          <p className="mt-2 text-gray-500 text-lg">Course Registration &amp; Scheduling Platform</p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {cards.map((card) => (
            <Link
              key={card.title}
              to={card.href}
              className="block bg-white border border-gray-200 rounded-2xl p-6 hover:border-gray-400 hover:shadow-sm transition"
            >
              <p className="text-lg font-semibold text-gray-900">{card.title}</p>
              <p className="text-sm text-gray-500 mt-2">{card.description}</p>
            </Link>
          ))}
        </div>

        <p className="text-center text-sm text-gray-400 mt-8">
          Use your institutional credentials or a manual profile to continue.
        </p>
      </div>
    </div>
  );
}
