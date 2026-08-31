import { LoginForm } from "./LoginForm";

export default function AdminLoginPage() {
  return (
    <LoginForm
      expectedRole="ADMIN"
      portalLabel="Administrator Portal"
      redirectTo="/admin/dashboard"
      accentDescription="Sign in with your PramaanScan administrator credentials to manage the platform."
    />
  );
}
