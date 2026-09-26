"use client";
import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { PenLine, RefreshCw, Save, ArrowLeft, Loader2, Check, X, Copy, Plus } from "lucide-react";





async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") : null;
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (workspaceId) headers["X-Workspace-Id"] = workspaceId;
  return fetch(url, { ...options, headers });
}


export default function PostsWorkspace({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const unwrappedParams = use(params);
  const productId = unwrappedParams.id;

  const [posts, setPosts] = useState<any[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [setupMode, setSetupMode] = useState(true);
  const [selectedIndex, setSelectedIndex] = useState(0);
  
  // Settings state
  const [settings, setSettings] = useState({
    num_posts: 3,
    tone: "Professional B2B",
    audience: "Business Owners",
    content_types: ["Product launch"],
    model: "gemini-3.5-flash"
  });

  const CONTENT_TYPE_OPTIONS = ["Product launch", "Feature", "Problem/Solution", "Educational", "Business benefit", "Product capability"];

  useEffect(() => {
    fetchPosts();
  }, [productId]);

  const fetchPosts = async () => {
    try {
      const res = await fetchWithAuth(`/api/products/${productId}/posts`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          setPosts(data);
          setSetupMode(false);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const generatePosts = async () => {
    setIsGenerating(true);
    try {
      const res = await fetchWithAuth(`/api/products/${productId}/posts/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
      });
      if (res.ok) {
        const data = await res.json();
        setPosts(data);
        setSetupMode(false);
        setSelectedIndex(0);
      }
    } catch (e) {
      console.error(e);
    }
    setIsGenerating(false);
  };

  const savePosts = async () => {
    setIsSaving(true);
    try {
      const res = await fetchWithAuth(`/api/products/${productId}/posts`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(posts)
      });
      if (res.ok) {
        const data = await res.json();
        setPosts(data);
      }
    } catch (e) {
      console.error(e);
    }
    setIsSaving(false);
  };

  const updateSelectedPost = (field: string, value: string) => {
    const updated = [...posts];
    updated[selectedIndex] = { ...updated[selectedIndex], [field]: value, status: "Draft" };
    setPosts(updated);
  };

  const updateStatus = (index: number, status: string) => {
    const updated = [...posts];
    updated[index] = { ...updated[index], status };
    setPosts(updated);
  };

  const duplicatePost = (index: number) => {
    const postToDuplicate = { ...posts[index], id: undefined, status: "Draft" };
    setPosts([...posts, postToDuplicate]);
  };

  const toggleContentType = (type: string) => {
    if (settings.content_types.includes(type)) {
      setSettings({ ...settings, content_types: settings.content_types.filter(t => t !== type) });
    } else {
      setSettings({ ...settings, content_types: [...settings.content_types, type] });
    }
  };

  if (setupMode) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col p-6 items-center">
        <div className="w-full max-w-3xl flex items-center mb-8 mt-10 gap-4">
           <button onClick={() => router.back()} className="p-2 bg-white rounded-full shadow-sm hover:bg-gray-50 text-gray-600">
             <ArrowLeft size={20} />
           </button>
           <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
             <PenLine className="text-blue-600" />
             LinkedIn Post Generation Setup
           </h1>
        </div>

        <div className="bg-white w-full max-w-3xl rounded-2xl shadow-sm border border-gray-200 p-8">
          <div className="mb-8">
            <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4">Content Types</h3>
            <div className="flex flex-wrap gap-3">
              {CONTENT_TYPE_OPTIONS.map(type => (
                <button
                  key={type}
                  onClick={() => toggleContentType(type)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    settings.content_types.includes(type) 
                      ? 'bg-blue-600 text-white shadow-md' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-8 mb-8">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Target Audience</label>
              <input 
                type="text" 
                value={settings.audience}
                onChange={(e) => setSettings({...settings, audience: e.target.value})}
                className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Tone of Voice</label>
              <select 
                value={settings.tone}
                onChange={(e) => setSettings({...settings, tone: e.target.value})}
                className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option>Professional B2B</option>
                <option>Casual & Engaging</option>
                <option>Authoritative</option>
                <option>Storytelling</option>
              </select>
            </div>
          </div>

          <div className="mb-8">
            <label className="block text-sm font-bold text-gray-700 mb-2">Number of Posts</label>
            <div className="flex items-center gap-4">
              <input 
                type="range" 
                min="1" max="10" 
                value={settings.num_posts}
                onChange={(e) => setSettings({...settings, num_posts: parseInt(e.target.value)})}
                className="flex-1"
              />
              <span className="font-bold text-xl text-blue-600 w-8">{settings.num_posts}</span>
            </div>
          </div>

          <button 
            onClick={generatePosts} disabled={isGenerating || settings.content_types.length === 0}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-4 rounded-xl shadow-md transition-all flex items-center justify-center gap-2 text-lg"
          >
            {isGenerating ? <Loader2 className="animate-spin" /> : <RefreshCw />}
            Generate Posts
          </button>
        </div>
      </div>
    );
  }

  const selectedPost = posts[selectedIndex];

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 hover:bg-gray-100 rounded-lg text-gray-600">
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <PenLine size={20} className="text-blue-600" />
            LinkedIn Posts Workspace
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setSetupMode(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors text-sm"
          >
            <Plus size={16} /> New Generation
          </button>
          <button 
            onClick={savePosts} disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg font-medium transition-colors text-sm shadow-sm"
          >
            <Save size={16} /> Save Changes
          </button>
          <button 
            onClick={() => { savePosts(); router.push("/"); }}
            className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold transition-colors text-sm shadow-sm"
          >
            <Check size={16} /> Done
          </button>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Left: List */}
        <div className="w-1/4 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4 border-b border-gray-100">
            <h2 className="font-bold text-gray-700">All Posts ({posts.length})</h2>
          </div>
          <div className="divide-y divide-gray-100">
            {posts.map((post, idx) => (
              <div 
                key={idx}
                onClick={() => setSelectedIndex(idx)}
                className={`p-4 cursor-pointer transition-colors ${selectedIndex === idx ? 'bg-blue-50 border-l-4 border-blue-600' : 'hover:bg-gray-50 border-l-4 border-transparent'}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-gray-500 uppercase">{post.topic || "Post"}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    post.status === 'Approved' ? 'bg-green-100 text-green-700' :
                    post.status === 'Rejected' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {post.status || 'Draft'}
                  </span>
                </div>
                <p className="text-sm font-medium text-gray-900 line-clamp-2">{post.hook}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Center: Editor */}
        <div className="w-2/4 bg-gray-50 border-r border-gray-200 p-6 overflow-y-auto">
          {selectedPost && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden animate-in fade-in zoom-in-95">
              <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <div className="font-bold text-gray-700">Editor</div>
                <div className="flex gap-2">
                  <button onClick={() => duplicatePost(selectedIndex)} className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded" title="Duplicate">
                    <Copy size={18} />
                  </button>
                  <button onClick={() => updateStatus(selectedIndex, 'Rejected')} className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded" title="Reject">
                    <X size={18} />
                  </button>
                  <button onClick={() => updateStatus(selectedIndex, 'Approved')} className="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded" title="Approve">
                    <Check size={18} />
                  </button>
                </div>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Topic</label>
                  <input 
                    type="text" 
                    value={selectedPost.topic || ""}
                    onChange={(e) => updateSelectedPost("topic", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 outline-none" 
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Hook</label>
                  <textarea 
                    rows={2}
                    value={selectedPost.hook || ""}
                    onChange={(e) => updateSelectedPost("hook", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 outline-none resize-none" 
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Body</label>
                  <textarea 
                    rows={8}
                    value={selectedPost.body || ""}
                    onChange={(e) => updateSelectedPost("body", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 outline-none resize-none" 
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Call to Action</label>
                  <input 
                    type="text" 
                    value={selectedPost.cta || ""}
                    onChange={(e) => updateSelectedPost("cta", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 outline-none" 
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Hashtags</label>
                  <input 
                    type="text" 
                    value={selectedPost.hashtags || ""}
                    onChange={(e) => updateSelectedPost("hashtags", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 outline-none text-blue-600" 
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: LinkedIn Preview */}
        <div className="w-1/4 bg-gray-100 p-6 overflow-y-auto flex justify-center">
          {selectedPost && (
            <div className="w-full max-w-sm bg-white rounded-xl shadow border border-gray-200 overflow-hidden self-start">
              <div className="p-4 border-b border-gray-100">
                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider text-center">LinkedIn Preview</h3>
              </div>
              <div className="p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 bg-gray-200 rounded-full flex-shrink-0"></div>
                  <div>
                    <h4 className="font-bold text-sm text-gray-900">Your Company</h4>
                    <p className="text-xs text-gray-500">Just now • 🌐</p>
                  </div>
                </div>
                
                <div className="text-sm text-gray-800 whitespace-pre-wrap font-sans">
                  {selectedPost.hook && <p className="mb-2 font-medium">{selectedPost.hook}</p>}
                  {selectedPost.body && <p className="mb-2">{selectedPost.body}</p>}
                  {selectedPost.cta && <p className="mb-2">{selectedPost.cta}</p>}
                  {selectedPost.hashtags && <p className="text-blue-600 font-medium">{selectedPost.hashtags}</p>}
                </div>
              </div>
              
              <div className="bg-gray-50 p-3 border-t border-gray-100 flex justify-between text-gray-500 text-xs font-medium">
                <span className="flex items-center gap-1 hover:bg-gray-200 px-2 py-1 rounded cursor-pointer">👍 Like</span>
                <span className="flex items-center gap-1 hover:bg-gray-200 px-2 py-1 rounded cursor-pointer">💬 Comment</span>
                <span className="flex items-center gap-1 hover:bg-gray-200 px-2 py-1 rounded cursor-pointer">🔁 Repost</span>
                <span className="flex items-center gap-1 hover:bg-gray-200 px-2 py-1 rounded cursor-pointer">✉️ Send</span>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
