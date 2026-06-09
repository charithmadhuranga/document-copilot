import { FormEvent, useState } from "react";
import { useAuth } from "@/hooks/useAuth";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const { signUp } = useAuth();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await signUp(email, password);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    }
  }

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center space-y-4 p-8">
          <h1 className="text-2xl font-bold">Check your email</h1>
          <p className="text-gray-600">A confirmation link has been sent to {email}.</p>
          <a href="/login" className="text-blue-600 hover:underline">Back to sign in</a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4 p-8">
        <h1 className="text-2xl font-bold">Create account</h1>
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full rounded border px-3 py-2"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full rounded border px-3 py-2"
        />
        <button type="submit" className="w-full rounded bg-blue-600 py-2 text-white font-medium hover:bg-blue-700">
          Sign up
        </button>
        <p className="text-sm text-center">
          <a href="/login" className="text-blue-600 hover:underline">Already have an account?</a>
        </p>
      </form>
    </div>
  );
}
