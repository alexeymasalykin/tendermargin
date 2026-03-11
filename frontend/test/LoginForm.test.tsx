import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { LoginForm } from "@/components/auth/LoginForm"

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }))
vi.mock("@/lib/api", () => ({
  api: { auth: { login: vi.fn().mockResolvedValue({}) } }
}))

it("shows email and password fields", () => {
  render(<LoginForm />)
  expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/пароль/i)).toBeInTheDocument()
})

it("shows validation error for empty submit", async () => {
  render(<LoginForm />)
  await userEvent.click(screen.getByRole("button", { name: /войти/i }))
  expect(await screen.findByText(/введите email/i)).toBeInTheDocument()
})
