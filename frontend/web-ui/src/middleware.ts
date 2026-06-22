/**
 * [PHASE3] Next.js middleware — protects routes from unauthenticated access
 * Redirects unauthenticated users to /login (production only)
 */
import { withAuth } from "next-auth/middleware"

export default withAuth(
  function middleware() {
    // Authenticated — let the request through
  },
  {
    callbacks: {
      authorized: ({ token, req }) => {
        // Allow all access in dev mode
        if (process.env.NODE_ENV !== "production") return true
        return !!token
      },
    },
    pages: {
      signIn: "/login",
    },
  }
)

export const config = {
  matcher: [
    "/((?!api|login|register|_next/static|_next/image|favicon.ico|manifest.json|sw.js).*)",
  ],
}
