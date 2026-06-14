/**
 * [PHASE3] NextAuth.js — main handler
 * Routes all /api/auth/* requests.
 * Uses credentials provider that authenticates against backend.
 */
import NextAuth, { NextAuthOptions } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Adam Prism",
      credentials: {
        username: { label: "Username or Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) {
          return null
        }
        try {
          const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              username_or_email: credentials.username,
              password: credentials.password,
            }),
          })
          if (!res.ok) return null
          const data = await res.json()
          if (data.access_token) {
            return {
              id: data.user_id,
              email: data.email || credentials.username,
              name: data.email || credentials.username,
              accessToken: data.access_token,
              refreshToken: data.refresh_token,
            }
          }
          return null
        } catch {
          return null
        }
      },
    }),
  ],
  session: {
    strategy: "jwt",
    maxAge: 7 * 24 * 60 * 60, // 7 days
  },
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = (user as any).accessToken
        token.refreshToken = (user as any).refreshToken
        token.userId = user.id
      }
      return token
    },
    async session({ session, token }) {
      ;(session as any).accessToken = token.accessToken
      ;(session as any).userId = token.userId
      return session
    },
  },
  secret: process.env.NEXTAUTH_SECRET || "change-me-in-production-use-32-chars-min",
}

export default NextAuth(authOptions)
