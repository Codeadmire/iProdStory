"use client";
import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { BriefcaseBusiness, Check, RefreshCw, Save, ArrowLeft, Loader2 } from "lucide-react";





async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") : null;
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (workspaceId) headers["X-Workspace-Id"] = workspaceId;
  return fetch(url, { ...options, headers });
}


export default function ProductPageGenerator({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const unwrappedParams = use(params);
  const productId = unwrappedParams.id;

  const [productPage, setProductPage] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // Load existing or mock
  useEffect(() => {
    fetchProductPage();
  }, [productId]);

  const fetchProductPage = async () => {
    try {
      const res = await fetchWithAuth(`/api/products/${productId}/product-page`);
      if (res.ok) {
        const data = await res.json();
        setProductPage(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const generatePage = async () => {
    setIsGenerating(true);
    try {
      const res = await fetchWithAuth(`/api/products/${productId}/product-page`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: "gemini-1.5-flash-latest" })
      });
      if (res.ok) {
        const data = await res.json();
        setProductPage(data);
      }
    } catch (e) {
      console.error(e);
    }
    setIsGenerating(false);
  };

  const savePage = async (status: string = "Draft") => {
    if (!productPage) return;
    setIsSaving(true);
    try {
      const res = await fetchWithAuth(`/api/products/${productId}/product-page`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...productPage, status })
      });
      if (res.ok) {
        const data = await res.json();
        setProductPage(data);
      }
    } catch (e) {
      console.error(e);
    }
    setIsSaving(false);
  };

  if (!productPage && !isGenerating) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="bg-white max-w-lg w-full rounded-2xl shadow-xl p-10 text-center">
          <div className="w-20 h-20 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
            <BriefcaseBusiness size={40} />
          </div>
          <h2 className="text-2xl font-bold mb-4">LinkedIn Product Page</h2>
          <p className="text-gray-500 mb-8">Generate your complete product listing from your approved product intelligence.</p>
          <button 
            onClick={generatePage}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-xl shadow-md transition-all flex items-center justify-center gap-2"
          >
            Generate Product Page ✨
          </button>
          <button onClick={() => router.back()} className="mt-4 text-sm text-gray-500 hover:text-gray-700">Cancel</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 hover:bg-gray-100 rounded-lg text-gray-600">
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <BriefcaseBusiness size={20} className="text-blue-600" />
              LinkedIn Product Page
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                productPage?.status === 'Approved' ? 'bg-green-100 text-green-700' :
                productPage?.status === 'In Review' ? 'bg-yellow-100 text-yellow-700' :
                'bg-gray-100 text-gray-600'
              }`}>
                {productPage?.status || 'Draft'}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={generatePage} disabled={isGenerating}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors text-sm"
          >
            {isGenerating ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
            Regenerate
          </button>
          <button 
            onClick={() => savePage("Draft")} disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg font-medium transition-colors text-sm shadow-sm"
          >
            <Save size={16} />
            Save Draft
          </button>
          <button 
            onClick={() => { savePage("Approved"); router.push("/"); }} disabled={isSaving}
            className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold transition-colors text-sm shadow-sm"
          >
            <Check size={16} />
            Approve & Continue
          </button>
        </div>
      </header>

      <main className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Left: Preview */}
        <div className="lg:w-1/2 p-6 lg:p-10 overflow-y-auto bg-gray-100 flex justify-center">
          <div className="w-full max-w-md bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden self-start animate-in fade-in zoom-in-95">
            <div className="h-32 bg-slate-800 relative">
              <div className="absolute -bottom-10 left-6 p-1 bg-white rounded-xl shadow-sm">
                <div className="w-20 h-20 bg-blue-50 rounded-lg flex items-center justify-center border border-gray-100">
                  <BriefcaseBusiness size={32} className="text-blue-500" />
                </div>
              </div>
            </div>
            
            <div className="pt-14 px-6 pb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-1">{productPage?.name || "Product Name"}</h2>
              <p className="text-gray-600 font-medium mb-4">{productPage?.tagline || "Your product tagline goes here."}</p>
              
              <div className="flex gap-2 mb-6">
                <button className="bg-blue-600 text-white px-5 py-1.5 rounded-full font-semibold text-sm">Visit website</button>
                <button className="bg-white border border-gray-300 text-gray-700 px-5 py-1.5 rounded-full font-semibold text-sm">Follow</button>
              </div>
              
              <div className="mb-6">
                <h3 className="font-bold text-gray-900 mb-2">About</h3>
                <p className="text-gray-700 text-sm whitespace-pre-wrap">{productPage?.description}</p>
              </div>
              
              <div className="mb-6">
                <h3 className="font-bold text-gray-900 mb-2">Target Audience</h3>
                <p className="text-gray-700 text-sm bg-gray-50 inline-block px-3 py-1 rounded-md">{productPage?.target_audience}</p>
              </div>
              
              <div>
                <h3 className="font-bold text-gray-900 mb-2">Key Highlights</h3>
                <div className="text-sm text-gray-700 whitespace-pre-wrap pl-2 border-l-2 border-blue-200">
                  {productPage?.highlights}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Editable Fields */}
        <div className="lg:w-1/2 bg-white border-l border-gray-200 overflow-y-auto">
          {isGenerating ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-400">
              <Loader2 size={48} className="animate-spin mb-4 text-blue-500" />
              <p>Analyzing product intelligence...</p>
            </div>
          ) : (
            <div className="p-8 max-w-2xl mx-auto space-y-6">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Product Name</label>
                <input 
                  type="text" 
                  value={productPage?.name || ""}
                  onChange={(e) => setProductPage({...productPage, name: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                />
              </div>
              
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Tagline</label>
                <input 
                  type="text" 
                  value={productPage?.tagline || ""}
                  onChange={(e) => setProductPage({...productPage, tagline: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                />
              </div>
              
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Description</label>
                <textarea 
                  rows={4}
                  value={productPage?.description || ""}
                  onChange={(e) => setProductPage({...productPage, description: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none" 
                />
              </div>
              
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Website</label>
                <input 
                  type="text" 
                  value={productPage?.website || ""}
                  onChange={(e) => setProductPage({...productPage, website: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-blue-600" 
                />
              </div>
              
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Target Audience</label>
                <input 
                  type="text" 
                  value={productPage?.target_audience || ""}
                  onChange={(e) => setProductPage({...productPage, target_audience: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                />
              </div>
              
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Product Highlights</label>
                <textarea 
                  rows={5}
                  value={productPage?.highlights || ""}
                  onChange={(e) => setProductPage({...productPage, highlights: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none" 
                />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
