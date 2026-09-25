"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { ArrowRight, Lock, Mail, User, Briefcase, Loader2, Layers } from "lucide-react";
import Link from "next/link";

export default function RegisterPage() {
  const router = useRouter();
  
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    workspace_name: "",
    password: "",
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await api.post<{ access_token: string; workspace_id: string }>("/api/auth/register", formData);
      
      // Save auth data
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("workspace_id", data.workspace_id);
      
      // Redirect to dashboard/home
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white flex items-center justify-center p-4 selection:bg-violet-500/30">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[10%] -left-[10%] w-[40%] h-[40%] rounded-full bg-violet-600/20 blur-[120px]" />
        <div className="absolute bottom-[10%] -right-[10%] w-[50%] h-[50%] rounded-full bg-indigo-600/10 blur-[120px]" />
      </div>

      <div className="w-full max-w-md relative z-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-violet-500/20">
            <Layers className="text-white" size={24} />
          </div>
          <h1 className="text-3xl font-semibold tracking-tight">Create your Workspace</h1>
          <p className="text-gray-400 mt-2 text-sm text-center">Set up your account and multi-tenant workspace to get started.</p>
        </div>

        <div className="bg-white/5 border border-white/10 p-8 rounded-2xl backdrop-blur-xl shadow-2xl">
          <form onSubmit={handleRegister} className="space-y-4">
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm flex items-center">
                {error}
              </div>
            )}
            
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300 ml-1">Full Name</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                  <User size={18} />
                </div>
                <input 
                  type="text" 
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all placeholder:text-gray-600"
                  placeholder="Steve Jobs"
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300 ml-1">Email Address</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                  <Mail size={18} />
                </div>
                <input 
                  type="email" 
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all placeholder:text-gray-600"
                  placeholder="steve@apple.com"
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300 ml-1">Workspace Name</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                  <Briefcase size={18} />
                </div>
                <input 
                  type="text" 
                  name="workspace_name"
                  value={formData.workspace_name}
                  onChange={handleChange}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all placeholder:text-gray-600"
                  placeholder="Apple Inc."
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
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all placeholder:text-gray-600"
                  placeholder="••••••••"
                  required
                  minLength={8}
                />
              </div>
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-gradient-to-r from-violet-500 to-indigo-600 hover:from-violet-400 hover:to-indigo-500 text-white font-medium py-3 rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-violet-500/25 disabled:opacity-50 disabled:cursor-not-allowed group mt-4"
            >
              {loading ? <Loader2 className="animate-spin" size={20} /> : (
                <>
                  Create Workspace
                  <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-white/10 text-center">
            <p className="text-gray-400 text-sm">
              Already have an account?{" "}
              <Link href="/login" className="text-violet-400 hover:text-violet-300 font-medium transition-colors">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
