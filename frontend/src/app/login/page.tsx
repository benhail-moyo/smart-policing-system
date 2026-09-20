"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, setAuth, getStoredUser, type AuthUser } from "@/lib/client";
import {
  Shield,
  UserPlus,
  LogIn,
  Car,
  Users,
  Loader2,
  User,
  KeyRound,
  RefreshCw,
  ArrowLeft,
  Eye,
  EyeOff,
  Check,
  X,
  BadgeCheck,
  Building2,
} from "lucide-react";

type AuthResponse = {
  token?: string;
  access_token?: string;
  user?: AuthUser;
  requires_otp?: boolean;
  message?: string;
  masked_email?: string;
  user_id?: number;
  role?: string;
  force_number?: string;
};

// Force Number validation regex: 6 digits followed by 1 uppercase letter
const FORCE_NUMBER_REGEX = /^\d{6}[A-Z]$/;

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [loginRole, setLoginRole] = useState<"officer" | "community">("officer");
  
  // Form fields
  const [forceNumber, setForceNumber] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [registerRole, setRegisterRole] = useState<"community" | "officer">("community");

  // OTP state
  const [otpCode, setOtpCode] = useState("");
  const [requiresOtp, setRequiresOtp] = useState(false);
  const [otpMessage, setOtpMessage] = useState<string | null>(null);
  const [maskedEmail, setMaskedEmail] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);

  useEffect(() => {
    const user = getStoredUser();
    if (user && user.id && (user.email || user.officer_id)) {
      router.replace("/");
    }
  }, [router]);

  // Password criteria checking logic
  const hasMinLength = password.length >= 8;
  const hasUppercase = /[A-Z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>\-_=+[\]\\/`~;']/.test(password);

  const checkSimilarity = () => {
    if (!password) return true;
    const pwLower = password.toLowerCase();
    const tokens: string[] = [];

    if (name) {
      name.split(/[\s._\-@]+/).forEach((t) => {
        if (t.trim().length >= 3) tokens.push(t.trim().toLowerCase());
      });
    }
    if (email && email.includes("@")) {
      const userPart = email.split("@")[0];
      userPart.split(/[\s._\-+]+/).forEach((t) => {
        if (t.trim().length >= 3) tokens.push(t.trim().toLowerCase());
      });
    }
    if (forceNumber) {
      const fn = forceNumber.trim().toLowerCase();
      if (fn.length >= 3) tokens.push(fn);
      const digits = fn.replace(/\D/g, "");
      if (digits.length >= 4) tokens.push(digits);
    }

    for (const token of tokens) {
      if (pwLower.includes(token)) return false;
    }
    return true;
  };

  const isNotSimilar = checkSimilarity();
  const isPasswordValid =
    hasMinLength && hasUppercase && hasNumber && hasSpecial && isNotSimilar;

  const passedCriteriaCount = [
    hasMinLength,
    hasUppercase,
    hasNumber,
    hasSpecial,
    isNotSimilar && password.length > 0,
  ].filter(Boolean).length;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (requiresOtp) {
        // Step 2: Submit credentials + OTP code
        const payload: Record<string, string> = {
          password,
          otp_code: otpCode.trim(),
        };
        if (forceNumber) {
          payload.force_number = forceNumber.trim().toUpperCase();
        } else {
          payload.email = email.trim().toLowerCase();
        }

        const res = await api<AuthResponse>("/api/auth/login", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        const token = res.token || res.access_token;
        if (token && res.user) {
          setAuth(token, res.user);
          router.replace("/");
          return;
        } else {
          setError(res.message || "Failed to verify authentication code");
        }
      } else if (mode === "login") {
        // Step 1: Login
        const payload: Record<string, string> = { password };

        if (loginRole === "officer") {
          const cleanFn = forceNumber.trim().toUpperCase();
          if (!FORCE_NUMBER_REGEX.test(cleanFn)) {
            setError("Force Number must be 6 digits followed by a capital letter (e.g. 123456X, 084512A).");
            setLoading(false);
            return;
          }
          payload.force_number = cleanFn;
        } else {
          if (!email) {
            setError("Email is required for community sign in.");
            setLoading(false);
            return;
          }
          payload.email = email.trim().toLowerCase();
        }

        const res = await api<AuthResponse>("/api/auth/login", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        // If 2FA OTP is required (Officers / Admins)
        if (res.requires_otp) {
          setRequiresOtp(true);
          setMaskedEmail(res.masked_email || null);
          setOtpMessage(res.message || `A verification code was sent to ${res.masked_email || "your email"}`);
          setError(null);
          return;
        }

        // Direct login success (Community)
        const token = res.token || res.access_token;
        if (token && res.user) {
          setAuth(token, res.user);
          router.replace("/");
        } else {
          setError("Login failed. No token received.");
        }
      } else {
        // Register Mode
        if (registerRole === "officer") {
          const cleanFn = forceNumber.trim().toUpperCase();
          if (!FORCE_NUMBER_REGEX.test(cleanFn)) {
            setError("Force Number must be 6 digits followed by a capital letter (e.g. 123456X, 084512A).");
            setLoading(false);
            return;
          }
        }

        if (!isPasswordValid) {
          setError("Please ensure your password meets all 5 security requirements.");
          setLoading(false);
          return;
        }

        if (password !== confirmPassword) {
          setError("Passwords do not match.");
          setLoading(false);
          return;
        }

        const payload = {
          name: name.trim(),
          email: email.trim().toLowerCase(),
          password,
          role: registerRole,
          ...(registerRole === "officer" && { force_number: forceNumber.trim().toUpperCase() }),
        };

        const res = await api<AuthResponse>("/api/auth/register", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        // Switch to login tab upon successful registration
        setMode("login");
        if (registerRole === "officer") {
          setLoginRole("officer");
        } else {
          setLoginRole("community");
        }
        setError(null);
        setOtpMessage("Account created successfully! Please sign in.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function resendOtp() {
    setError(null);
    setLoading(true);
    try {
      const payload: Record<string, string> = { password };
      if (forceNumber) {
        payload.force_number = forceNumber.trim().toUpperCase();
      } else {
        payload.email = email.trim().toLowerCase();
      }

      const res = await api<AuthResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setOtpMessage(res.message || `A new verification code was sent to ${res.masked_email || "your email"}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resend code");
    } finally {
      setLoading(false);
    }
  }

  async function demoLogin(type: "officer" | "admin" | "community") {
    setError(null);
    setSeeding(true);
    setRequiresOtp(false);
    setOtpCode("");

    try {
      // Seed database before login
      await api("/api/seed", { method: "POST" }).catch(() => {});

      if (type === "officer") {
        setLoginRole("officer");
        setForceNumber("084512A");
        setPassword("Officer-2026!");
        const res = await api<AuthResponse>("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ force_number: "084512A", password: "Officer-2026!" }),
        });
        if (res.requires_otp) {
          setRequiresOtp(true);
          setMaskedEmail(res.masked_email || "officer@harare.gov.zw");
          setOtpMessage(res.message || "A verification code was sent to officer@harare.gov.zw");
        }
      } else if (type === "admin") {
        setLoginRole("officer");
        setForceNumber("123456X");
        setPassword("Smart-policing1!");
        const res = await api<AuthResponse>("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ force_number: "123456X", password: "Smart-policing1!" }),
        });
        if (res.requires_otp) {
          setRequiresOtp(true);
          setMaskedEmail(res.masked_email || "benhailmoyo7@gmail.com");
          setOtpMessage(res.message || "A verification code was sent to benhailmoyo7@gmail.com");
        }
      } else {
        setLoginRole("community");
        setEmail("community@harare.gov.zw");
        setPassword("Community-2026!");
        const res = await api<AuthResponse>("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ email: "community@harare.gov.zw", password: "Community-2026!" }),
        });
        const token = res.token || res.access_token;
        if (token && res.user) {
          setAuth(token, res.user);
          router.replace("/");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong during demo login");
    } finally {
      setSeeding(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-10 text-slate-100">
      <div className="w-full max-w-md">
        {/* Brand Header */}
        <div className="mb-6 text-center">
          <div className="flex justify-center">
            <Shield className="h-12 w-12 text-blue-400" />
          </div>
          <h1 className="mt-2 text-2xl font-bold tracking-tight">Harare Crime Watch</h1>
          <p className="text-sm text-slate-400">
            Smart Community Policing & Strategic Command
          </p>
        </div>

        {/* Main Card */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl backdrop-blur-sm">
          {requiresOtp ? (
            /* 2FA OTP Screen for Officers & Admins */
            <div>
              <div className="mb-5 text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/10 text-blue-400 ring-1 ring-blue-500/20">
                  <KeyRound className="h-6 w-6" />
                </div>
                <h2 className="text-lg font-semibold text-slate-100">Two-Factor Security Verification</h2>
                <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                  {otpMessage || `Enter the 6-digit OTP code sent to ${maskedEmail || "your registered email"}`}
                </p>
              </div>

              <form onSubmit={submit} className="space-y-4">
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-slate-300">
                    6-Digit Verification Code
                  </label>
                  <input
                    type="text"
                    inputMode="numeric"
                    autoFocus
                    maxLength={6}
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))}
                    placeholder="123456"
                    required
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-3 text-center font-mono text-2xl tracking-[0.4em] text-white outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
                  />
                </div>

                {error && (
                  <div className="rounded-lg bg-red-500/15 border border-red-500/30 px-3 py-2.5 text-xs text-red-300">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading || otpCode.length < 6}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50 transition"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <BadgeCheck className="h-4 w-4" />
                  )}
                  {loading ? "Verifying…" : "Verify Code & Sign In"}
                </button>
              </form>

              <div className="mt-5 flex items-center justify-between border-t border-slate-800 pt-3.5 text-xs">
                <button
                  type="button"
                  disabled={loading}
                  onClick={resendOtp}
                  className="flex items-center gap-1.5 text-slate-400 hover:text-blue-400 disabled:opacity-50 transition"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Resend OTP Code
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setRequiresOtp(false);
                    setOtpCode("");
                    setError(null);
                  }}
                  className="flex items-center gap-1 text-slate-400 hover:text-slate-200 transition"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Back to Sign In
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Mode Selector (Sign In vs Register) */}
              <div className="mb-5 flex rounded-lg bg-slate-800/80 p-1">
                {(["login", "register"] as const).map((m) => {
                  const active = mode === m;
                  const Icon = m === "login" ? LogIn : UserPlus;
                  return (
                    <button
                      key={m}
                      onClick={() => {
                        setMode(m);
                        setError(null);
                        setOtpMessage(null);
                      }}
                      className={`flex flex-1 items-center justify-center gap-1.5 rounded-md py-2 text-xs font-semibold uppercase tracking-wider transition ${
                        active
                          ? "bg-blue-600 text-white shadow"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <Icon className="h-3.5 w-3.5" />
                      {m === "login" ? "Sign In" : "Register"}
                    </button>
                  );
                })}
              </div>

              {/* Login Sub-tabs (Police/Admin vs Community) */}
              {mode === "login" && (
                <div className="mb-4 grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setLoginRole("officer");
                      setError(null);
                    }}
                    className={`flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-medium transition ${
                      loginRole === "officer"
                        ? "border-blue-500/50 bg-blue-500/10 text-blue-400 font-semibold"
                        : "border-slate-800 bg-slate-800/40 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <Building2 className="h-3.5 w-3.5" />
                    Police / Admin
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setLoginRole("community");
                      setError(null);
                    }}
                    className={`flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-medium transition ${
                      loginRole === "community"
                        ? "border-blue-500/50 bg-blue-500/10 text-blue-400 font-semibold"
                        : "border-slate-800 bg-slate-800/40 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <Users className="h-3.5 w-3.5" />
                    Community
                  </button>
                </div>
              )}

              {/* Register Role Selector */}
              {mode === "register" && (
                <div className="mb-4">
                  <label className="mb-1.5 block text-xs font-medium text-slate-300">
                    Account Type
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setRegisterRole("community")}
                      className={`flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-medium transition ${
                        registerRole === "community"
                          ? "border-blue-500/50 bg-blue-500/10 text-blue-400 font-semibold"
                          : "border-slate-800 bg-slate-800/40 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <Users className="h-3.5 w-3.5" />
                      Community Member
                    </button>
                    <button
                      type="button"
                      onClick={() => setRegisterRole("officer")}
                      className={`flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-medium transition ${
                        registerRole === "officer"
                          ? "border-blue-500/50 bg-blue-500/10 text-blue-400 font-semibold"
                          : "border-slate-800 bg-slate-800/40 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <Building2 className="h-3.5 w-3.5" />
                      Police Officer
                    </button>
                  </div>
                </div>
              )}

              {otpMessage && !error && (
                <div className="mb-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-3 py-2 text-xs text-emerald-400">
                  {otpMessage}
                </div>
              )}

              <form onSubmit={submit} className="space-y-3.5">
                {/* Mode: Login -> Officer */}
                {mode === "login" && loginRole === "officer" && (
                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-300">
                      Force Number
                    </label>
                    <input
                      type="text"
                      value={forceNumber}
                      onChange={(e) => setForceNumber(e.target.value.toUpperCase())}
                      placeholder="e.g. 084512A"
                      maxLength={7}
                      required
                      className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm uppercase tracking-wider outline-none focus:border-blue-500 font-mono transition"
                    />
                    <p className="mt-1 text-[11px] text-slate-400">
                      Must be 6 digits followed by a capital letter (e.g. 123456X)
                    </p>
                  </div>
                )}

                {/* Mode: Login -> Community */}
                {mode === "login" && loginRole === "community" && (
                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-300">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@example.com"
                      required
                      className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm outline-none focus:border-blue-500 transition"
                    />
                  </div>
                )}

                {/* Mode: Register fields */}
                {mode === "register" && (
                  <>
                    {registerRole === "officer" && (
                      <div>
                        <label className="mb-1 block text-xs font-medium text-slate-300">
                          Force Number (Official Police ID)
                        </label>
                        <input
                          type="text"
                          value={forceNumber}
                          onChange={(e) => setForceNumber(e.target.value.toUpperCase())}
                          placeholder="e.g. 084512A"
                          maxLength={7}
                          required
                          className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm uppercase tracking-wider outline-none focus:border-blue-500 font-mono transition"
                        />
                        <p className="mt-1 text-[11px] text-slate-400">
                          Format: 6 digits + 1 capital letter (123456X)
                        </p>
                      </div>
                    )}

                    <div>
                      <label className="mb-1 block text-xs font-medium text-slate-300">
                        Full Name
                      </label>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder={registerRole === "officer" ? "e.g. Officer Chikwava" : "e.g. Tendai Moyo"}
                        required
                        className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm outline-none focus:border-blue-500 transition"
                      />
                    </div>

                    <div>
                      <label className="mb-1 block text-xs font-medium text-slate-300">
                        {registerRole === "officer" ? "Official Email (for 2FA Security OTPs)" : "Email Address"}
                      </label>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="name@police.gov.zw"
                        required
                        className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm outline-none focus:border-blue-500 transition"
                      />
                    </div>
                  </>
                )}

                {/* Password input */}
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-300">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 pr-10 text-sm outline-none focus:border-blue-500 transition"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {/* Live Password Strength Meter in Register Mode */}
                {mode === "register" && password.length > 0 && (
                  <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 space-y-2">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-400">Password Security Policy</span>
                      <span
                        className={`font-semibold ${
                          passedCriteriaCount === 5
                            ? "text-emerald-400"
                            : passedCriteriaCount >= 3
                            ? "text-amber-400"
                            : "text-red-400"
                        }`}
                      >
                        {passedCriteriaCount === 5
                          ? "Strong"
                          : passedCriteriaCount >= 3
                          ? "Moderate"
                          : "Weak"}
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          passedCriteriaCount === 5
                            ? "bg-emerald-500 w-full"
                            : passedCriteriaCount >= 3
                            ? "bg-amber-500 w-3/5"
                            : "bg-red-500 w-1/5"
                        }`}
                      />
                    </div>

                    {/* Checklist of 5 rules */}
                    <div className="grid grid-cols-1 gap-1 text-[11px] pt-1">
                      <div className={`flex items-center gap-1.5 ${hasMinLength ? "text-emerald-400" : "text-slate-500"}`}>
                        {hasMinLength ? <Check className="h-3 w-3 text-emerald-400 shrink-0" /> : <X className="h-3 w-3 text-slate-500 shrink-0" />}
                        <span>At least 8 characters</span>
                      </div>
                      <div className={`flex items-center gap-1.5 ${hasUppercase ? "text-emerald-400" : "text-slate-500"}`}>
                        {hasUppercase ? <Check className="h-3 w-3 text-emerald-400 shrink-0" /> : <X className="h-3 w-3 text-slate-500 shrink-0" />}
                        <span>At least one capital letter (A-Z)</span>
                      </div>
                      <div className={`flex items-center gap-1.5 ${hasNumber ? "text-emerald-400" : "text-slate-500"}`}>
                        {hasNumber ? <Check className="h-3 w-3 text-emerald-400 shrink-0" /> : <X className="h-3 w-3 text-slate-500 shrink-0" />}
                        <span>At least one number (0-9)</span>
                      </div>
                      <div className={`flex items-center gap-1.5 ${hasSpecial ? "text-emerald-400" : "text-slate-500"}`}>
                        {hasSpecial ? <Check className="h-3 w-3 text-emerald-400 shrink-0" /> : <X className="h-3 w-3 text-slate-500 shrink-0" />}
                        <span>At least one special character (!@#$%^&*)</span>
                      </div>
                      <div className={`flex items-center gap-1.5 ${isNotSimilar ? "text-emerald-400" : "text-red-400"}`}>
                        {isNotSimilar ? <Check className="h-3 w-3 text-emerald-400 shrink-0" /> : <X className="h-3 w-3 text-red-400 shrink-0" />}
                        <span>Not similar to name, email, or Force Number</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Confirm Password in Register Mode */}
                {mode === "register" && (
                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-300">
                      Confirm Password
                    </label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      className={`w-full rounded-lg border bg-slate-800 px-3 py-2.5 text-sm outline-none transition ${
                        confirmPassword && confirmPassword !== password
                          ? "border-red-500 focus:border-red-500"
                          : "border-slate-700 focus:border-blue-500"
                      }`}
                    />
                    {confirmPassword && confirmPassword !== password && (
                      <p className="mt-1 text-[11px] text-red-400">Passwords do not match</p>
                    )}
                  </div>
                )}

                {error && (
                  <div className="rounded-lg bg-red-500/15 border border-red-500/30 px-3 py-2.5 text-xs text-red-300">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading || (mode === "register" && (!isPasswordValid || password !== confirmPassword))}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50 transition"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : mode === "login" ? (
                    <LogIn className="h-4 w-4" />
                  ) : (
                    <UserPlus className="h-4 w-4" />
                  )}
                  {loading
                    ? "Please wait…"
                    : mode === "login"
                    ? loginRole === "officer"
                      ? "Sign In (Force Number)"
                      : "Sign In (Community)"
                    : "Create Account"}
                </button>
              </form>

              {/* Quick Demo Access */}
              <div className="mt-6 border-t border-slate-800 pt-4">
                <p className="mb-2.5 text-center text-xs uppercase tracking-wider text-slate-500">
                  Quick Demo Access
                </p>
                <div className="grid gap-2">
                  <button
                    disabled={seeding}
                    onClick={() => demoLogin("officer")}
                    className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-800/70 px-3.5 py-2 text-xs hover:border-blue-500 hover:bg-slate-800 disabled:opacity-50 transition"
                  >
                    <div className="flex items-center gap-2">
                      <Car className="h-4 w-4 text-blue-400" />
                      <span className="font-medium text-slate-200">Patrol Officer</span>
                    </div>
                    <span className="font-mono text-[11px] text-slate-400">FN: 084512A</span>
                  </button>

                  <button
                    disabled={seeding}
                    onClick={() => demoLogin("admin")}
                    className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-800/70 px-3.5 py-2 text-xs hover:border-blue-500 hover:bg-slate-800 disabled:opacity-50 transition"
                  >
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-amber-400" />
                      <span className="font-medium text-slate-200">Command Admin</span>
                    </div>
                    <span className="font-mono text-[11px] text-slate-400">FN: 123456X</span>
                  </button>

                  <button
                    disabled={seeding}
                    onClick={() => demoLogin("community")}
                    className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-800/70 px-3.5 py-2 text-xs hover:border-blue-500 hover:bg-slate-800 disabled:opacity-50 transition"
                  >
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-emerald-400" />
                      <span className="font-medium text-slate-200">Community Member</span>
                    </div>
                    <span className="text-[11px] text-slate-400">Direct Sign In</span>
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
