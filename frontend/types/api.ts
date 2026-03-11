export interface User {
  id: string
  email: string
  name: string
}

export interface Project {
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
}

export type StepStatus = "not_started" | "in_progress" | "completed"

export interface ProjectProgress {
  smeta: { status: StepStatus; item_count?: number; total_sum?: number }
  materials: { status: StepStatus; filled?: number; total?: number }
  contractor: { status: StepStatus; filled?: number; total?: number }
  pricelist: { status: StepStatus }
  margin: { available: boolean; margin_pct?: number }
}

export interface ProjectDetail extends Project {
  progress: ProjectProgress
}

export interface SmetaItem {
  id: string
  number: number
  code: string
  name: string
  unit: string
  quantity: number
  unit_price: number
  total_price: number
  item_type: "work" | "material" | "equipment" | "mechanism" | "unknown"
  section: string
}

export interface Material {
  id: string
  name: string
  unit: string
  quantity: number
  smeta_total: number
  supplier_price: number | null
  supplier_total: number | null
}

export interface ContractorPrice {
  id: string
  smeta_item_id: string
  fsnb_code: string
  name: string
  unit: string
  quantity: number
  ceiling_total: number
  price: number | null
  total: number | null
}

export interface PricelistMatch {
  id: string
  material_id: string
  supplier_name: string | null
  supplier_price: number | null
  confidence: number | null
  status: "pending" | "accepted" | "rejected"
}

export interface MarginItem {
  name: string
  code: string
  item_type: string
  unit: string
  quantity: number
  ceiling_price: number
  cost_price: number
  margin: number
  margin_pct: number
  status: "green" | "yellow" | "red" | "loss"
}

export interface MarginResult {
  total_ceiling: number
  total_cost: number
  total_margin: number
  margin_pct: number
  min_profit: number
  max_discount_pct: number
  floor_price: number
  items: MarginItem[]
}

export type MarginStatus = "green" | "yellow" | "red" | "loss"

export interface ApiError {
  detail: string
  status?: number
}
