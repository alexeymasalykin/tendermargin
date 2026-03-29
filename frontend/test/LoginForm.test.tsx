import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { LoginForm } from "@/components/auth/LoginForm"

const loginMock = vi.fn().mockResolvedValue({})

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }))
vi.mock("@/lib/api", () => ({
  api: { auth: { login: (...args: unknown[]) => loginMock(...args) } }
}))

beforeEach(() => loginMock.mockReset().mockResolvedValue({}))

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

it("shows server error on failed login (401)", async () => {
  loginMock.mockRejectedValueOnce({ detail: "Неверный email или пароль" })

  render(<LoginForm />)

  await userEvent.type(screen.getByLabelText(/email/i), "test@example.com")
  await userEvent.type(screen.getByLabelText(/пароль/i), "wrongpassword")
  await userEvent.click(screen.getByRole("button", { name: /войти/i }))

  expect(await screen.findByText(/неверный email или пароль/i)).toBeInTheDocument()
})
