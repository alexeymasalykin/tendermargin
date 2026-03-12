import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

const PUBLIC_PATHS = ["/", "/login", "/register"]

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const isPublic = PUBLIC_PATHS.some(p => pathname === p || pathname.startsWith(p + "/"))
  const accessToken = request.cookies.get("access_token")
  const refreshToken = request.cookies.get("refresh_token")

  if (!isPublic && !accessToken) {
    // Try to refresh if we have a refresh token
    if (refreshToken) {
      try {
        const res = await fetch("http://fastapi:8000/api/v1/auth/refresh", {
          method: "POST",
          headers: { Cookie: `refresh_token=${refreshToken.value}` },
        })
        if (res.ok) {
          const response = NextResponse.next()
          for (const cookie of res.headers.getSetCookie()) {
            response.headers.append("Set-Cookie", cookie)
          }
          return response
        }
      } catch {
        // Refresh failed, fall through to redirect
      }
    }
    return NextResponse.redirect(new URL("/login", request.url))
  }

  if (accessToken && (pathname === "/login" || pathname === "/register")) {
    return NextResponse.redirect(new URL("/dashboard", request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api).*)"],
}
