/**
 * [PHASE3] Next.js middleware — protects routes from unauthenticated access
 * Redirects unauthenticated users to /login
 */
import { withAuth } from "next-auth/middleware"

export default withAuth(
  function middleware() {
    // Authenticated — let the request through
  },
  {
    callbacks: {
      authorized: ({ token }) => !!token,
    },
    pages: {
      signIn: "/login",
    },
  }
)

export const config = {
  // Protect these routes
  matcher: [
    "/((?!api|login|register|_next/static|_next/image|favicon.ico|manifest.json|sw.js).*)",
  ],
}
