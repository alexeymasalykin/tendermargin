import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { RegisterForm } from "@/components/auth/RegisterForm"

const registerMock = vi.fn().mockResolvedValue({})

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }))
vi.mock("@/lib/api", () => ({
  api: { auth: { register: (...args: unknown[]) => registerMock(...args) } }
}))

beforeEach(() => registerMock.mockReset().mockResolvedValue({}))

it("renders all form fields", () => {
  render(<RegisterForm />)
  expect(screen.getByLabelText(/имя/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/^пароль$/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/подтвердите пароль/i)).toBeInTheDocument()
  expect(screen.getByRole("button", { name: /создать аккаунт/i })).toBeInTheDocument()
})

it("shows server error on failed registration (422)", async () => {
  registerMock.mockRejectedValueOnce({ detail: "Email уже зарегистрирован" })

  render(<RegisterForm />)

  await userEvent.type(screen.getByLabelText(/имя/i), "Тест")
  await userEvent.type(screen.getByLabelText(/email/i), "test@example.com")
  await userEvent.type(screen.getByLabelText(/^пароль$/i), "password123")
  await userEvent.type(screen.getByLabelText(/подтвердите пароль/i), "password123")
  await userEvent.click(screen.getByRole("button", { name: /создать аккаунт/i }))

  expect(await screen.findByText(/email уже зарегистрирован/i)).toBeInTheDocument()
})
