import { useEffect, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { API, apiFetch, AuthContext } from "./auth";
import "./Auth.css";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [mode, setMode] = useState("login");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  useEffect(() => {
    if (!sessionStorage.getItem("atmograph_token")) { setChecking(false); return; }
    apiFetch("/api/auth/me").then(async (response) => {
      if (!response.ok) throw new Error();
      setUser(await response.json());
    }).catch(() => sessionStorage.removeItem("atmograph_token")).finally(() => setChecking(false));
  }, []);

  async function submit(event) {
    event.preventDefault();
    setBusy(true); setError("");
    const data = new FormData(event.currentTarget);
    const payload = { email: data.get("email"), password: data.get("password") };
    if (mode === "register") {
      payload.name = data.get("name");
      if (payload.password !== data.get("confirmPassword")) {
        setError("Passwords do not match");
        setBusy(false);
        return;
      }
    }
    try {
      const response = await fetch(`${API}/api/auth/${mode}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Authentication failed");
      sessionStorage.setItem("atmograph_token", result.access_token);
      setUser(result.user);
    } catch (requestError) { setError(requestError.message); }
    finally { setBusy(false); }
  }

  function logout() { sessionStorage.removeItem("atmograph_token"); setUser(null); }
  if (checking) return <div className="auth-page"><p>Verifying session…</p></div>;
  if (!user) return <main className="auth-page"><section className="auth-card"><div className="auth-brand"><span className="auth-orbit">A</span><div><h1>AtmoGraph</h1><p>Supply-chain intelligence control room</p></div></div><div className="auth-tabs"><button className={mode === "login" ? "active" : ""} onClick={() => { setMode("login"); setError(""); }}>Sign in</button><button className={mode === "register" ? "active" : ""} onClick={() => { setMode("register"); setError(""); }}>Create account</button></div><form onSubmit={submit}>{mode === "register" && <label>Full name<input name="name" minLength="2" required autoComplete="name" /></label>}<label>Email<input name="email" type="email" required autoComplete="email" /></label><label>Password<span className="password-field"><input name="password" type={showPassword ? "text" : "password"} minLength="10" required autoComplete={mode === "login" ? "current-password" : "new-password"} /><button type="button" className="password-toggle" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></span></label>{mode === "register" && <label>Confirm password<span className="password-field"><input name="confirmPassword" type={showConfirmPassword ? "text" : "password"} minLength="10" required autoComplete="new-password" /><button type="button" className="password-toggle" onClick={() => setShowConfirmPassword((value) => !value)} aria-label={showConfirmPassword ? "Hide confirmed password" : "Show confirmed password"}>{showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></span></label>}{error && <p className="auth-error" role="alert">{error}</p>}<button className="auth-submit" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}</button></form><small>Sessions expire after 30 minutes.</small></section></main>;
  return <AuthContext.Provider value={{ user, logout }}>{children}</AuthContext.Provider>;
}
