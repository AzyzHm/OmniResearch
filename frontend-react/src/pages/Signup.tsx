import { useState } from "react"
import { Link } from "react-router-dom"
import { CheckCircle2 } from "lucide-react"
import AuthLayout from "@/components/AuthLayout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { register } from "@/api/auth"
import { ApiError } from "@/lib/apiClient"

function validateUsername(value: string): string | null {
  const v = value.trim()
  if (v.length < 3) return "Username must be at least 3 characters."
  if (v.length > 50) return "Username must be at most 50 characters."
  if (!/^[a-zA-Z0-9_-]+$/.test(v)) {
    return "Username may only contain letters, digits, _ and -."
  }
  return null
}

function validatePassword(value: string): string | null {
  if (value.length < 8) return "Password must be at least 8 characters."
  return null
}

function Signup() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    const usernameError = validateUsername(username)
    if (usernameError) return setError(usernameError)

    const passwordError = validatePassword(password)
    if (passwordError) return setError(passwordError)

    if (password !== confirmPassword) {
      setError("Passwords don't match.")
      return
    }

    setIsSubmitting(true)
    try {
      await register({ username: username.trim(), password })
      setSubmitted(true)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError("Couldn't reach the server. Try again in a moment.")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <AuthLayout
        title="Account created"
        subtitle="One more step before you can log in."
      >
        <div className="rounded-xl border border-border bg-surface p-5">
          <CheckCircle2 className="size-6 text-teal" />
          <p className="mt-3 text-sm text-ink leading-relaxed">
            Your account has been created. An administrator needs to approve
            it before you can log in — this is usually quick.
          </p>
        </div>
        <p className="mt-6 text-sm text-muted-foreground text-center">
          <Link to="/login" className="text-ink font-medium hover:text-teal transition-colors">
            Back to log in
          </Link>
        </p>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Start organizing your research in one place."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="username">Username</Label>
          <Input
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            placeholder="yourusername"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            placeholder="At least 8 characters"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="confirmPassword">Confirm password</Label>
          <Input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            placeholder="••••••••"
          />
        </div>

        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Creating account..." : "Sign up"}
        </Button>
      </form>

      <p className="mt-6 text-sm text-muted-foreground text-center">
        Already have an account?{" "}
        <Link to="/login" className="text-ink font-medium hover:text-teal transition-colors">
          Log in
        </Link>
      </p>
    </AuthLayout>
  )
}

export default Signup