import { formatMoney, formatPercent } from "@/lib/utils"

describe("formatMoney", () => {
  it("formats integer with ru locale", () => {
    const result = formatMoney(1234567)
    expect(result).toMatch(/1.234.567|1 234 567|1\u00a0234\u00a0567/)
  })
})

describe("formatPercent", () => {
  it("formats to 1 decimal", () => {
    expect(formatPercent(22.857)).toBe("22.9%")
  })
})
