import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { KeyRound, User as UserIcon, Palette, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { getProfile, changePassword } from "@/api/profile";
import { useAuth } from "@/context/AuthContext";
import { useTheme, type Theme } from "@/context/ThemeContext";
import { initials, formatDateTime } from "@/lib/utils";
import { getApiErrorMessage } from "@/api/client";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Required"),
    new_password: z.string().min(8, "At least 8 characters"),
    confirm_password: z.string().min(1, "Required"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords don't match",
    path: ["confirm_password"],
  });

type PasswordForm = z.infer<typeof passwordSchema>;

export function ProfileSettings() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  const { data: profile, isLoading } = useQuery({ queryKey: ["profile"], queryFn: getProfile });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PasswordForm>({ resolver: zodResolver(passwordSchema) });

  const mutation = useMutation({
    mutationFn: (values: PasswordForm) => changePassword(values.current_password, values.new_password),
    onSuccess: () => {
      setPasswordSuccess(true);
      reset();
      toast({ title: "Password changed", variant: "success" });
      window.setTimeout(() => setPasswordSuccess(false), 3000);
    },
    onError: (err) => {
      toast({ title: "Could not change password", description: getApiErrorMessage(err), variant: "destructive" });
    },
  });

  return (
    <div>
      <PageHeader title="Profile & Settings" description="Manage your account details, security, and appearance." />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardContent className="flex flex-col items-center p-6 text-center">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="text-lg">{initials(user?.full_name)}</AvatarFallback>
            </Avatar>
            <h3 className="mt-4 font-display text-base font-semibold">{user?.full_name}</h3>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
            <span className="mt-3 rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
              {user?.role === "ADMIN" ? "Administrator" : "Institution Authority"}
            </span>
            <Separator className="my-5" />
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            ) : (
              <dl className="w-full space-y-2.5 text-left text-xs">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Member since</dt>
                  <dd className="font-medium">{formatDateTime(profile?.created_at)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Last login</dt>
                  <dd className="font-medium">{formatDateTime(profile?.last_login_at)}</dd>
                </div>
                {user?.issuer_id && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Issuer ID</dt>
                    <dd className="font-medium">{user.issuer_id}</dd>
                  </div>
                )}
              </dl>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <UserIcon className="h-4 w-4 text-primary" /> Account
              </CardTitle>
              <CardDescription>Your basic account information (read-only for now).</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Full Name</Label>
                <Input value={user?.full_name ?? ""} disabled />
              </div>
              <div className="space-y-1.5">
                <Label>Email</Label>
                <Input value={user?.email ?? ""} disabled />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <KeyRound className="h-4 w-4 text-primary" /> Change Password
              </CardTitle>
              <CardDescription>Choose a strong, unique password.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="current_password">Current Password</Label>
                  <Input id="current_password" type="password" {...register("current_password")} />
                  {errors.current_password && <p className="text-xs text-destructive">{errors.current_password.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="new_password">New Password</Label>
                  <Input id="new_password" type="password" {...register("new_password")} />
                  {errors.new_password && <p className="text-xs text-destructive">{errors.new_password.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="confirm_password">Confirm New Password</Label>
                  <Input id="confirm_password" type="password" {...register("confirm_password")} />
                  {errors.confirm_password && <p className="text-xs text-destructive">{errors.confirm_password.message}</p>}
                </div>
                <div className="sm:col-span-2">
                  <Button type="submit" loading={mutation.isPending}>
                    {passwordSuccess ? "Password Updated" : "Update Password"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Palette className="h-4 w-4 text-primary" /> Appearance
              </CardTitle>
              <CardDescription>Choose how PramaanScan looks on this device.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-3">
                {(["light", "dark", "system"] as Theme[]).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTheme(t)}
                    className={cn(
                      "rounded-xl border-2 px-4 py-3 text-sm font-medium capitalize transition-colors",
                      theme === t ? "border-primary bg-primary/5 text-primary" : "border-border hover:border-primary/40"
                    )}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
