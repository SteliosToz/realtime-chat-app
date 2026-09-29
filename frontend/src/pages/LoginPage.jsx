import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await login(email, password)
      navigate('/chat')
    } catch (err) {
      setError('Λάθος email ή password')
    }
  }

  return (
    <div className="min-h-screen bg-bg-main flex items-center justify-center">
      <form
        onSubmit={handleSubmit}
        className="bg-bg-sidebar border border-border rounded-lg p-8 w-full max-w-sm"
      >
        <h1 className="text-text-header text-2xl font-bold mb-6 text-center">
          Σύνδεση
        </h1>

        {error && (
          <p className="bg-red-500/10 text-red-400 text-sm rounded p-2 mb-4">
            {error}
          </p>
        )}

        <label className="block text-text-secondary text-sm mb-1">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full bg-bg-elevated text-text-primary rounded p-2 mb-4 outline-none border border-border focus:border-accent"
        />

        <label className="block text-text-secondary text-sm mb-1">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full bg-bg-elevated text-text-primary rounded p-2 mb-6 outline-none border border-border focus:border-accent"
        />

        <button
          type="submit"
          className="w-full bg-accent hover:bg-accent-hover text-white font-semibold py-2 rounded"
        >
          Σύνδεση
        </button>

        <p className="text-text-secondary text-sm text-center mt-4">
          Δεν έχεις λογαριασμό;{' '}
          <Link to="/register" className="text-accent hover:underline">
            Εγγραφή
          </Link>
        </p>
      </form>
    </div>
  )
}

export default LoginPage