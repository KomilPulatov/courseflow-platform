export default function LoginPlaceholder({ role }: { role: string }) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <p className="text-gray-400">{role} login - coming soon</p>
      </div>
    </div>
  )
}
