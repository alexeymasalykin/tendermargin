import { render, screen } from "@testing-library/react"
import { Sidebar } from "@/components/layout/Sidebar"

vi.mock("next/navigation", () => ({ usePathname: () => "/dashboard" }))
vi.mock("next/link", () => ({
  default: ({ href, children, className, ...props }: { href: string; children: React.ReactNode; className?: string; [key: string]: unknown }) => (
    <a href={href} className={className} {...props}>{children}</a>
  ),
}))

it("highlights active link", () => {
  render(<Sidebar />)
  const link = screen.getByText("Проекты").closest("a")
  expect(link?.className).toContain("text-primary")
})
