import { useMemo, useState } from 'react'
import { FaHospital, FaTicketAlt, FaUser } from 'react-icons/fa'
import { useLocation, useNavigate } from 'react-router-dom'
import { AppHeader } from '../components/AppHeader.jsx'
import { useAuth } from '../context/AuthContext.jsx'

function firstErrorMessage(error) {
  if (!error) {
    return 'No hem pogut completar el registre.'
  }

  if (typeof error === 'string') {
    return error
  }

  const firstEntry = Object.values(error)[0]

  if (Array.isArray(firstEntry)) {
    return String(firstEntry[0])
  }

  if (typeof firstEntry === 'string') {
    return firstEntry
  }

  return 'No hem pogut completar el registre.'
}

function registrationPathFromSearch(search) {
  const params = new URLSearchParams(search)
  return params.get('token') ? 'join_organisation' : 'independent'
}

export function TherapistRegisterPage() {
  const { registerTherapist } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const initialToken = useMemo(() => new URLSearchParams(location.search).get('token') || '', [location.search])
  const initialEmail = useMemo(() => new URLSearchParams(location.search).get('email') || '', [location.search])
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: initialEmail,
    license_number: '',
    specialty: '',
    registration_path: registrationPathFromSearch(location.search),
    organisation_name: '',
    invitation_token: initialToken,
  })
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function buildPayload() {
    const payload = {
      first_name: form.first_name,
      last_name: form.last_name,
      email: form.email,
      license_number: form.license_number,
      specialty: form.specialty,
      registration_path: form.registration_path,
    }

    if (form.registration_path === 'create_clinic') {
      payload.organisation_name = form.organisation_name
    }

    if (form.registration_path === 'join_organisation') {
      payload.invitation_token = form.invitation_token
    }

    return payload
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await registerTherapist(buildPayload())
      navigate('/login', {
        replace: true,
        state: { message: 'Registre creat correctament. Revisa el correu per activar el compte.' },
      })
    } catch (requestError) {
      setError(firstErrorMessage(requestError.response?.data || requestError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="screen-shell">
      <AppHeader />
      <div className="screen-grid">
        <aside className="screen-card hero-panel" style={{ display: "flex", flexDirection: "column", gap: "30px", justifyContent: "flex-start" }}>
          <div className="hero-copy">
            <p className="eyebrow">Reflexia</p>
            <h1>Registre de terapeutes</h1>
            <p className="hero-lead">Tria el teu tipus de registre per començar.</p>
          </div>
        </aside>

        <div style={{ display: "grid", gap: "20px" }}>
            <section className="screen-card form-panel">
          <div className="panel-heading">
            <p className="eyebrow" style={{ margin: "0" }}>Alta terapeuta</p>
          </div>

          {error ? <div className="error-banner">{error}</div> : null}

          <form className="form-stack" onSubmit={handleSubmit}>
            <div className="path-selector" role="radiogroup" aria-label="Tipus de registre" style={{ marginBottom: "1rem" }}>
              <button
                type="button"
                className={`path-option ${form.registration_path === 'independent' ? 'path-option--active' : ''}`}
                onClick={() => updateField('registration_path', 'independent')}
                role="radio"
                aria-checked={form.registration_path === 'independent'}
              >
                <FaUser />
                Independent
              </button>
              <button
                type="button"
                className={`path-option ${form.registration_path === 'create_clinic' ? 'path-option--active' : ''}`}
                onClick={() => updateField('registration_path', 'create_clinic')}
                role="radio"
                aria-checked={form.registration_path === 'create_clinic'}
              >
                <FaHospital />
                Clínica
              </button>
              <button
                type="button"
                className={`path-option ${form.registration_path === 'join_organisation' ? 'path-option--active' : ''}`}
                onClick={() => updateField('registration_path', 'join_organisation')}
                role="radio"
                aria-checked={form.registration_path === 'join_organisation'}
              >
                <FaTicketAlt />
                Invitació
              </button>
            </div>

            <div className="inline-fields">
              <div className="field-group">
                <label htmlFor="first_name">Nom</label>
                <input
                  id="first_name"
                  value={form.first_name}
                  onChange={(event) => updateField('first_name', event.target.value)}
                  required
                />
              </div>
              <div className="field-group">
                <label htmlFor="last_name">Cognoms</label>
                <input
                  id="last_name"
                  value={form.last_name}
                  onChange={(event) => updateField('last_name', event.target.value)}
                  required
                />
              </div>
            </div>

            <div className="field-group">
              <label htmlFor="email">Correu electrònic</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={form.email}
                onChange={(event) => updateField('email', event.target.value)}
                readOnly={Boolean(initialEmail)}
                required
              />
            </div>

            <div className="inline-fields">
              <div className="field-group">
                <label htmlFor="license_number">Núm. col·legiat</label>
                <input
                  id="license_number"
                  value={form.license_number}
                  onChange={(event) => updateField('license_number', event.target.value)}
                  required
                />
              </div>
              <div className="field-group">
                <label htmlFor="specialty">Especialitat</label>
                <input
                  id="specialty"
                  value={form.specialty}
                  onChange={(event) => updateField('specialty', event.target.value)}
                  required
                />
              </div>
            </div>

            {form.registration_path === 'create_clinic' ? (
              <div className="field-group">
                <label htmlFor="organisation_name">Nom de la clínica</label>
                <input
                  id="organisation_name"
                  value={form.organisation_name}
                  onChange={(event) => updateField('organisation_name', event.target.value)}
                  required
                />
              </div>
            ) : null}

            {form.registration_path === 'join_organisation' ? (
              <div className="field-group">
                <label htmlFor="invitation_token">Token d&apos;invitació</label>
                <input
                  id="invitation_token"
                  value={form.invitation_token}
                  onChange={(event) => updateField('invitation_token', event.target.value)}
                  required
                />
              </div>
            ) : null}

            <div className="button-row" style={{ marginTop: "1rem", justifyContent: "center" }}>
              <button className="button" type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Registrant...' : 'Crear compte'}
              </button>
            </div>
          </form>
        </section>

        <section className="screen-card form-panel">
            <div className="panel-heading">
              <p className="eyebrow" style={{ margin: "0" }}>Ja tens un compte?</p>
              <p style={{ margin: "0 0 1rem 0" }}>Inicia sessió per accedir al teu compte.</p>
              <button className="button" style={{ justifySelf: "center" }} onClick={() => navigate('/login')}>
                Inicia sessió
              </button>
          </div>
        </section>
        </div>
      </div>
    </div>
  )
}
