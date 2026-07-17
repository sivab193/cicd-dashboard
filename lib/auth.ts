import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";
import type { GitHubProfile } from "next-auth/providers/github";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    GitHub({
      authorization: { params: { scope: "read:user repo" } },
    }),
  ],
  callbacks: {
    async signIn({ profile }) {
      const allowedLogin = process.env.ALLOWED_GITHUB_LOGIN;
      if (!allowedLogin) return true;
      return (profile as GitHubProfile | undefined)?.login === allowedLogin;
    },
    async jwt({ token, account }) {
      if (account?.access_token) {
        token.accessToken = account.access_token;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
});
