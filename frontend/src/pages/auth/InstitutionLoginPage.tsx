import { LoginForm } from "./LoginForm";

export default function InstitutionLoginPage() {
  return (
    <LoginForm
      expectedRole="AUTHORITY"
      portalLabel="Institution Portal"
      redirectTo="/institution/dashboard"
      accentDescription="Sign in with your issuing authority credentials to manage signed communications."
    />
  );
}
