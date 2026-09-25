"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { ArrowRight, Lock, Mail, Loader2, Layers } from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await api.post<{ access_token: string; workspace_id: string }>("/api/auth/login", {
        email,
        password,
      });
      
      // Save auth data
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("workspace_id", data.workspace_id);
      
      // Redirect to dashboard/home
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white flex items-center justify-center p-4 selection:bg-indigo-500/30">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[25%] -left-[10%] w-[50%] h-[50%] rounded-full bg-indigo-600/20 blur-[120px]" />
        <div className="absolute top-[60%] -right-[10%] w-[40%] h-[40%] rounded-full bg-violet-600/10 blur-[120px]" />
      </div>

      <div className="w-full max-w-md relative z-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-indigo-500/20">
            <Layers className="text-white" size={24} />
          </div>
          <h1 className="text-3xl font-semibold tracking-tight">Welcome back</h1>
          <p className="text-gray-400 mt-2 text-sm text-center">Log in to your workspace and continue building your product story.</p>
        </div>

        <div className="bg-white/5 border border-white/10 p-8 rounded-2xl backdrop-blur-xl shadow-2xl">
          <form onSubmit={handleLogin} className="space-y-5">
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm flex items-center">
                {error}
              </div>
            )}
            
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300 ml-1">Email Address</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                  <Mail size={18} />
                </div>
                <input 
                  type="email" 
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all placeholder:text-gray-600"
                  placeholder="name@company.com"
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300 ml-1">Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                  <Lock size={18} />
                </div>
                <input 
                  type="password" 
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all placeholder:text-gray-600"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 text-white font-medium py-3 rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/25 disabled:opacity-50 disabled:cursor-not-allowed group mt-2"
            >
              {loading ? <Loader2 className="animate-spin" size={20} /> : (
                <>
                  Sign In
                  <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-white/10 text-center">
            <p className="text-gray-400 text-sm">
              Don't have a workspace yet?{" "}
              <Link href="/register" className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
                Create one now
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
