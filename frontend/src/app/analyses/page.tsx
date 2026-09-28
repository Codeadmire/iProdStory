"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { User, LogOut, ArrowRight, Clock, Plus } from "lucide-react";

async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") : null;
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (workspaceId) headers["X-Workspace-Id"] = workspaceId;
  return fetch(url, { ...options, headers });
}

export default function AnalysesHistory() {
  const router = useRouter();
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    fetchWithAuth(`/api/products`).then(async (res) => {
      if (res.ok) {
        const data = await res.json();
        setAnalyses(data);
      }
      setIsLoading(false);
    });
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("workspace_id");
    router.push("/login");
  };

  const handleOpenAnalysis = (id: string) => {
    sessionStorage.setItem("activeProductId", id);
    sessionStorage.setItem("journeyStep", "review");
    router.push("/");
  };

  const filteredAndSortedAnalyses = analyses
    .filter(a => 
      (a.name && a.name.toLowerCase().includes(searchQuery.toLowerCase())) || 
      (a.base_url && a.base_url.toLowerCase().includes(searchQuery.toLowerCase()))
    )
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  return (
    <div className="flex h-screen bg-[#06040A] text-white font-light tracking-wide font-sans overflow-hidden relative">
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-indigo-900/20 blur-[150px]"></div>
        <div className="absolute bottom-[20%] -right-[10%] w-[40%] h-[40%] rounded-full bg-amber-900/10 blur-[150px]"></div>
      </div>
      <div className="flex w-full h-full relative z-10">
      
      {/* LEFT SIDEBAR */}
      <div className="w-64 bg-white/5 backdrop-blur-xl border-r border-white/10 flex flex-col hidden md:flex">
        <div className="p-6 border-b border-white/5">
          <Link href="/">
            <h1 className="text-xl font-bold flex items-center gap-2 cursor-pointer">
              🚀 Product Marketing AI
            </h1>
          </Link>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-8 text-sm">
          <div>
            <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3">Workspace</h3>
            <ul className="space-y-1">
              <li><Link href="/" className="block w-full text-left px-3 py-2 text-white/70 hover:bg-white/[0.02] rounded-md">New Analysis</Link></li>
              <li><button className="w-full text-left px-3 py-2 bg-amber-500/10 border-l-2 border-amber-500 text-amber-400 font-medium rounded-md">Analyses History</button></li>
              <li><button className="w-full text-left px-3 py-2 text-white/70 hover:bg-white/[0.02] rounded-md">Products <span className="float-right text-[10px] bg-white/5 px-2 py-0.5 rounded text-white/40">Soon</span></button></li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3">Create</h3>
            <ul className="space-y-1">
              <li><button className="w-full text-left px-3 py-2 text-white/70 hover:bg-white/[0.02] rounded-md">LinkedIn <span className="float-right text-[10px] bg-white/5 px-2 py-0.5 rounded text-white/40">Soon</span></button></li>
              <li><button className="w-full text-left px-3 py-2 text-white/70 hover:bg-white/[0.02] rounded-md">Social Posts <span className="float-right text-[10px] bg-white/5 px-2 py-0.5 rounded text-white/40">Soon</span></button></li>
              <li><button className="w-full text-left px-3 py-2 text-white/70 hover:bg-white/[0.02] rounded-md">Images <span className="float-right text-[10px] bg-white/5 px-2 py-0.5 rounded text-white/40">Soon</span></button></li>
              <li><button className="w-full text-left px-3 py-2 text-white/70 hover:bg-white/[0.02] rounded-md">Videos <span className="float-right text-[10px] bg-white/5 px-2 py-0.5 rounded text-white/40">Soon</span></button></li>
            </ul>
          </div>

          <div>
            <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3">Library</h3>
            <ul className="space-y-1">
              <li><button className="w-full text-left px-3 py-2 text-white/70 hover:bg-white/[0.02] rounded-md">Assets <span className="float-right text-[10px] bg-white/5 px-2 py-0.5 rounded text-white/40">Soon</span></button></li>
              <li><button className="w-full text-left px-3 py-2 text-white/70 hover:bg-white/[0.02] rounded-md">Content <span className="float-right text-[10px] bg-white/5 px-2 py-0.5 rounded text-white/40">Soon</span></button></li>
            </ul>
          </div>
        </div>
        
        <div className="p-4 border-t border-white/5">
          <button className="w-full text-left px-3 py-2 text-white/70 hover:bg-white/[0.02] rounded-md text-sm font-medium mb-4 flex items-center gap-2">
            ⚙ Settings
          </button>
          
          <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
                <User size={16} className="text-white" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-medium text-white">Alex</span>
                <span className="text-[10px] text-gray-400">Pro Plan</span>
              </div>
            </div>
            <button onClick={handleLogout} className="text-gray-400 hover:text-red-400 transition-colors" title="Logout">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <header className="bg-white/5 backdrop-blur-xl border-b border-white/10 px-8 py-6 flex items-center justify-between z-10">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1">Analyses History</h1>
            <p className="text-gray-400 text-sm">View and manage all your past product analyses, generated content, and campaigns.</p>
          </div>
          <Link href="/">
            <button className="bg-amber-500 hover:bg-amber-600 text-white font-medium px-4 py-2 rounded-lg transition-colors flex items-center gap-2">
              <Plus size={16} />
              New Analysis
            </button>
          </Link>
        </header>

        <main className="flex-1 overflow-y-auto p-8 z-10">
          <div className="max-w-5xl mx-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-64 text-amber-500">
                <div className="animate-spin h-8 w-8 border-2 border-amber-500/50 rounded-full border-t-transparent"></div>
              </div>
            ) : analyses.length === 0 ? (
              <div className="bg-white/5 border border-white/10 rounded-2xl p-12 text-center">
                <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4 text-white/30">
                  <Clock size={32} />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">No analyses yet</h3>
                <p className="text-gray-400 mb-6">You haven't analyzed any products yet. Start your first analysis to generate marketing content.</p>
                <Link href="/">
                  <button className="bg-amber-500 hover:bg-amber-600 text-white font-medium px-6 py-3 rounded-lg transition-colors inline-flex items-center gap-2">
                    Start Analysis
                  </button>
                </Link>
              </div>
            ) : (
              <div className="flex flex-col gap-6">
                <input 
                  type="text" 
                  placeholder="Filter by product name or URL..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500/50 transition-colors"
                />
                
                {filteredAndSortedAnalyses.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    No analyses match your search.
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {filteredAndSortedAnalyses.map((analysis) => (
                  <div 
                    key={analysis.id} 
                    className="bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 transition-all rounded-xl p-6 flex items-center justify-between group cursor-pointer"
                    onClick={() => handleOpenAnalysis(analysis.id)}
                  >
                    <div>
                      <h3 className="text-lg font-bold text-white mb-1 group-hover:text-amber-400 transition-colors">{analysis.name || analysis.base_url}</h3>
                      <p className="text-sm text-gray-400 flex items-center gap-4">
                        <span>{analysis.base_url}</span>
                        <span className="flex items-center gap-1">
                          <Clock size={12} />
                          {new Date(analysis.created_at).toLocaleString()}
                        </span>
                      </p>
                    </div>
                    <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-amber-500 group-hover:bg-amber-500/20 transition-colors">
                      <ArrowRight size={20} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
      </div>
    </div>
  );
}
