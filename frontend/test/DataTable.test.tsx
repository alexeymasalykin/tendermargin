import { render, screen } from "@testing-library/react"
import { DataTable } from "@/components/tables/DataTable"
import { createColumnHelper } from "@tanstack/react-table"

const col = createColumnHelper<{ name: string; value: number }>()
const columns = [
  col.accessor("name", { header: "Название" }),
  col.accessor("value", { header: "Значение" }),
]
const data = [{ name: "Штукатурка", value: 84000 }]

it("renders headers and data", () => {
  render(<DataTable columns={columns} data={data} />)
  expect(screen.getByText("Название")).toBeInTheDocument()
  expect(screen.getByText("Штукатурка")).toBeInTheDocument()
  expect(screen.getByText("84000")).toBeInTheDocument()
})

it("shows empty state when no data", () => {
  render(<DataTable columns={columns} data={[]} emptyText="Нет данных" />)
  expect(screen.getByText("Нет данных")).toBeInTheDocument()
})
