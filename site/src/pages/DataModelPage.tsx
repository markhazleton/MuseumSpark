export { default } from '../components/docs/DataModelDocument'

interface DataSourceProps {
  name: string
  description: string
  fields: string
}

function DataSource({ name, description, fields }: DataSourceProps) {
  return (
    <div className="rounded-lg bg-white border border-indigo-200 p-4">
      <h3 className="font-bold text-indigo-900 mb-2">{name}</h3>
      <p className="text-sm text-slate-700 mb-3">{description}</p>
      <div className="text-xs text-slate-600">
        <span className="font-semibold">Key Fields:</span>
        <div className="mt-1 text-slate-700">{fields}</div>
      </div>
    </div>
  )
}
