import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ApiError } from '../lib/api';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo iniciar sesión');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background:
          'radial-gradient(circle at 20% 20%, rgba(245,166,35,0.06), transparent 40%), var(--bg)',
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          width: 340,
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 12,
          padding: 32,
        }}
      >
        <div style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 22 }}>
            Despacho<span style={{ color: 'var(--accent)' }}>.</span>
          </h1>
          <p style={{ color: 'var(--text-dim)', fontSize: 13, marginTop: 6 }}>
            Panel de despachador — inicia sesión para continuar
          </p>
        </div>

        <label htmlFor="login-email" style={{ display: 'block', fontSize: 12, color: 'var(--text-dim)', marginBottom: 6 }}>
          Correo
        </label>
        <input
          id="login-email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={inputStyle}
          autoFocus
        />

        <label htmlFor="login-password" style={{ display: 'block', fontSize: 12, color: 'var(--text-dim)', margin: '16px 0 6px' }}>
          Contraseña
        </label>
        <input
          id="login-password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={inputStyle}
        />

        {error && (
          <div style={{ color: 'var(--danger)', fontSize: 13, marginTop: 14 }}>{error}</div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            marginTop: 22,
            padding: '10px 0',
            background: 'var(--accent)',
            color: '#1a1204',
            border: 'none',
            borderRadius: 'var(--radius)',
            fontWeight: 600,
            fontSize: 14,
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? 'Ingresando…' : 'Ingresar'}
        </button>
      </form>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '9px 10px',
  background: 'var(--bg)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--text)',
  fontSize: 14,
};
