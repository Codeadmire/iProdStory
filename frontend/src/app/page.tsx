"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { BriefcaseBusiness, PenLine, Image, Clapperboard } from "lucide-react";

// Types
interface PageData {
  id: string;
  url: string;
  title: string;
  depth: number;
  status: number | string;
  error_message?: string;
  h1?: string;
  h2?: string;
}

interface FeatureData {
  id: string;
  name: string;
  confidence: string;
}

interface ScreenshotData {
  id: string;
  page_id: string;
  image_path: string;
}

type JourneyStep = 'home' | 'discover' | 'understand' | 'create' | 'review' | 'publish';

export default function Home() {
  const router = useRouter();
  // App States
  const [url, setUrl] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [maxPages, setMaxPages] = useState(50);
  const [maxDepth, setMaxDepth] = useState(3);
  const [aiModel, setAiModel] = useState("gemini-1.5-flash-latest");
  
  // Data States
  const [product, setProduct] = useState<any>(null);
  const [crawlJob, setCrawlJob] = useState<any>(null);
  const [features, setFeatures] = useState<FeatureData[]>([]);
  const [pages, setPages] = useState<PageData[]>([]);
  const [screenshots, setScreenshots] = useState<ScreenshotData[]>([]);
  const [modules, setModules] = useState<any[]>([]);
  const [isAnalyzingAI, setIsAnalyzingAI] = useState(false);
  
  // Journey States
  const [journeyStep, setJourneyStep] = useState<JourneyStep>('home');
  const [viewingDetails, setViewingDetails] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [pageSearch, setPageSearch] = useState("");
  const [previewImage, setPreviewImage] = useState<string | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (crawlJob && (crawlJob.status === "Started" || crawlJob.status === "RUNNING" || crawlJob.status === "PENDING")) {
      interval = setInterval(() => {
        refreshDashboard();
      }, 2000);
    } else if (crawlJob && (crawlJob.status === "COMPLETED" || crawlJob.status === "COMPLETED_WITH_WARNINGS")) {
      // Refresh one last time just to be sure we have everything
      refreshDashboard();
    }
    return () => clearInterval(interval);
  }, [crawlJob?.status]);

  const analyzeProduct = async () => {
    if (!url) return;
    setJourneyStep('discover');
    setViewingDetails(false);
    try {
      const prodRes = await fetch("http://localhost:8000/api/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const prodData = await prodRes.json();
      setProduct(prodData);

      const crawlRes = await fetch(`http://localhost:8000/api/products/${prodData.id}/crawl`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ max_pages: maxPages, max_depth: maxDepth, timeout: 30000 })
      });
      const crawlData = await crawlRes.json();
      setCrawlJob(crawlData);
    } catch (e) {
      console.error(e);
    }
  };

  async function refreshDashboard() {
    if (!product || !crawlJob) return;
    try {
      const jobRes = await fetch(`http://localhost:8000/api/crawls/${crawlJob.job_id || crawlJob.id}`);
      const jobData = await jobRes.json();
      setCrawlJob((prev: any) => ({ ...prev, ...jobData }));

      const pagesRes = await fetch(`http://localhost:8000/api/products/${product.id}/pages`);
      setPages(await pagesRes.json());

      const featsRes = await fetch(`http://localhost:8000/api/products/${product.id}/features`);
      setFeatures(await featsRes.json());
      
      const exportRes = await fetch(`http://localhost:8000/api/crawls/${crawlJob.job_id || crawlJob.id}/export`);
      const exportData = await exportRes.json();
      setScreenshots(exportData.screenshots || []);
    } catch (e) {
      console.error(e);
    }
  };

  const [isGeneratingCampaign, setIsGeneratingCampaign] = useState(false);
  const [mediaAssets, setMediaAssets] = useState<string[]>([]);
  
  const [editingMode, setEditingMode] = useState<'product' | 'posts' | null>(null);
  const [campaignData, setCampaignData] = useState({
    headline: "Inventory & Business Management Platform",
    about: "A complete business management platform that brings inventory, purchasing, sales, delivery, and financial operations into one connected system.",
    posts: [
      "Struggling to keep track of stock across multiple warehouses? 📦\n\nWe just mapped out exactly how modern enterprises are solving this.\n\nIntroducing our new platform — the connected system for inventory, sales, and purchasing.",
      "Are you tired of manually syncing your sales and inventory data? 🤦‍♂️\n\nCheck out the new automated workflows we just released!"
    ]
  });

  const [campaignId, setCampaignId] = useState<string | null>(null);

  const startCampaignGeneration = async () => {
    setIsGeneratingCampaign(true);
    
    if (product) {
      try {
        // 1. Generate Media
        const mediaResponse = await fetch(`http://localhost:8000/api/products/${product.id}/media`, { method: 'POST' });
        const mediaData = await mediaResponse.json();
        if (mediaData.assets) {
          setMediaAssets(mediaData.assets);
        }
        
        // 2. Generate Campaign via LLM
        const campaignResponse = await fetch(`http://localhost:8000/api/products/${product.id}/campaign`, { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: aiModel })
        });
        const campaignResData = await campaignResponse.json();
        if (campaignResData) {
          setCampaignId(campaignResData.id);
          setCampaignData({
            headline: campaignResData.headline,
            about: campaignResData.about,
            posts: campaignResData.posts
          });
        }
      } catch (err) {
        console.error("Campaign generation error", err);
      }
    }
    
    setIsGeneratingCampaign(false);
    setJourneyStep('review');
  };

  const [isLinkedInAuth, setIsLinkedInAuth] = useState(false);
  const [publishStatus, setPublishStatus] = useState<'idle' | 'publishing' | 'published'>('idle');
  const [postUrl, setPostUrl] = useState('');

  const handleLinkedInPublish = async () => {
    if (!isLinkedInAuth) {
      try {
        const res = await fetch(`http://localhost:8000/api/linkedin/auth/url`);
        const data = await res.json();
        // Mock auth completion
        setIsLinkedInAuth(true);
      } catch(e) {}
      return;
    }
    
    if (!product) return;
    setPublishStatus('publishing');
    try {
      const res = await fetch(`http://localhost:8000/api/products/${product.id}/publish`, { method: 'POST' });
      const data = await res.json();
      setPublishStatus('published');
      setPostUrl(data.linkedin_post_url);
    } catch (e) {
      setPublishStatus('idle');
    }
  };

  const startAiAnalysis = async () => {
    if (!product) return;
    setIsAnalyzingAI(true);
    try {
      await fetch(`http://localhost:8000/api/products/${product.id}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: aiModel })
      });
      
      // Poll for modules
      const pollModules = setInterval(async () => {
        const res = await fetch(`http://localhost:8000/api/products/${product.id}/modules`);
        const data = await res.json();
        if (data && data.length > 0) {
          setModules(data);
          clearInterval(pollModules);
          setIsAnalyzingAI(false);
          setJourneyStep('create');
        }
      }, 3000);
      
    } catch (e) {
      console.error(e);
      setIsAnalyzingAI(false);
    }
  };

  const exportJSON = async () => {
    if (!crawlJob) return;
    const res = await fetch(`http://localhost:8000/api/crawls/${crawlJob.job_id || crawlJob.id}/export`);
    const data = await res.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const dlUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = dlUrl;
    a.download = `crawl_export_${crawlJob.job_id || crawlJob.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const isCompleted = crawlJob?.status === "COMPLETED" || crawlJob?.status === "COMPLETED_WITH_WARNINGS";
  const isFailed = crawlJob?.status === "FAILED";
  const progressPercent = crawlJob ? Math.min(100, Math.round((crawlJob.pages_processed / crawlJob.max_pages) * 100)) : 0;
  
  const filteredPages = pages.filter(p => 
    p.url.toLowerCase().includes(pageSearch.toLowerCase()) || 
    (p.title && p.title.toLowerCase().includes(pageSearch.toLowerCase()))
  );

  const steps = [
    { id: 'discover', label: 'Discover', num: 1 },
    { id: 'understand', label: 'Understand', num: 2 },
    { id: 'create', label: 'Create', num: 3 },
    { id: 'review', label: 'Review', num: 4 },
    { id: 'publish', label: 'Publish', num: 5 }
  ];

  const getCurrentStepIndex = () => {
    const idx = steps.findIndex(s => s.id === journeyStep);
    return idx === -1 ? 0 : idx;
  };
  const currIdx = getCurrentStepIndex();

  return (
    <div className="flex h-screen bg-[#F8FAFC] text-gray-900 font-sans overflow-hidden">
      
      {/* LEFT SIDEBAR */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col hidden md:flex">
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-xl font-bold flex items-center gap-2">
            🚀 Product Marketing AI
          </h1>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-8 text-sm">
          <div>
            <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">Workspace</h3>
            <ul className="space-y-1">
              <li><button className="w-full text-left px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-md">Dashboard <span className="float-right text-[10px] bg-gray-100 px-2 py-0.5 rounded text-gray-400">Soon</span></button></li>
              <li><button className="w-full text-left px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-md">Products <span className="float-right text-[10px] bg-gray-100 px-2 py-0.5 rounded text-gray-400">Soon</span></button></li>
              <li><button className="w-full text-left px-3 py-2 bg-blue-50 text-blue-700 font-medium rounded-md">Analyses</button></li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">Create</h3>
            <ul className="space-y-1">
              <li><button className="w-full text-left px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-md">LinkedIn <span className="float-right text-[10px] bg-gray-100 px-2 py-0.5 rounded text-gray-400">Soon</span></button></li>
              <li><button className="w-full text-left px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-md">Social Posts <span className="float-right text-[10px] bg-gray-100 px-2 py-0.5 rounded text-gray-400">Soon</span></button></li>
              <li><button className="w-full text-left px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-md">Images <span className="float-right text-[10px] bg-gray-100 px-2 py-0.5 rounded text-gray-400">Soon</span></button></li>
              <li><button className="w-full text-left px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-md">Videos <span className="float-right text-[10px] bg-gray-100 px-2 py-0.5 rounded text-gray-400">Soon</span></button></li>
            </ul>
          </div>

          <div>
            <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">Library</h3>
            <ul className="space-y-1">
              <li><button className="w-full text-left px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-md">Assets <span className="float-right text-[10px] bg-gray-100 px-2 py-0.5 rounded text-gray-400">Soon</span></button></li>
              <li><button className="w-full text-left px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-md">Content <span className="float-right text-[10px] bg-gray-100 px-2 py-0.5 rounded text-gray-400">Soon</span></button></li>
            </ul>
          </div>
        </div>
        
        <div className="p-4 border-t border-gray-100">
          <button className="w-full text-left px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-md text-sm font-medium">⚙ Settings</button>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        
        {/* TOP HEADER: JOURNEY INDICATOR */}
        {journeyStep !== 'home' && (
          <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-center z-10">
            <div className="flex items-center gap-2 md:gap-4 w-full max-w-4xl justify-between">
              {steps.map((step, idx) => (
                <div key={step.id} className="flex items-center">
                  <div 
                    className={`flex items-center gap-2 ${idx < currIdx ? 'text-blue-600 font-medium cursor-pointer hover:underline' : idx === currIdx ? 'text-gray-900 font-bold' : 'text-gray-300 pointer-events-none'}`}
                    onClick={() => { if (idx < currIdx) setJourneyStep(step.id as JourneyStep); }}
                  >
                    <span className={`flex items-center justify-center w-6 h-6 rounded-full text-xs ${idx < currIdx ? 'bg-blue-100 text-blue-700' : idx === currIdx ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-400'}`}>
                      {idx < currIdx ? '✓' : step.num}
                    </span>
                    <span className="hidden md:inline">{step.label}</span>
                  </div>
                  {idx < steps.length - 1 && (
                    <div className="hidden md:block w-8 lg:w-16 h-px mx-4 bg-gray-200" />
                  )}
                </div>
              ))}
            </div>
          </header>
        )}

        {/* MAIN SCROLL AREA */}
        <main className="flex-1 overflow-y-auto p-8 relative">
          
          {/* SCREEN 1: NEW PRODUCT (HOME) */}
          {journeyStep === 'home' && (
            <div className="max-w-2xl mx-auto mt-20 text-center animate-in fade-in zoom-in-95 duration-500">
              <h2 className="text-5xl font-extrabold tracking-tight mb-4 text-gray-900">
                Turn Your Product<br/>Into Marketing Content
              </h2>
              <p className="text-xl text-gray-500 mb-12 max-w-lg mx-auto">
                Enter your product URL. We'll discover your product, understand what it does, and create LinkedIn-ready content.
              </p>
              
              <div className="bg-white p-2 rounded-2xl shadow-lg border border-gray-100 mb-6 relative flex items-center transition-all focus-within:ring-4 focus-within:ring-blue-100">
                <span className="pl-4 text-xl">🔗</span>
                <input 
                  type="text" 
                  placeholder="https://yourproduct.com" 
                  className="w-full p-4 text-lg bg-transparent border-none outline-none text-gray-800 placeholder-gray-400"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && analyzeProduct()}
                />
                <button 
                  onClick={analyzeProduct}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3.5 rounded-xl transition-all shadow-md shrink-0 flex items-center gap-2"
                >
                  ✨ Analyze My Product
                </button>
              </div>
              
              <p className="text-sm font-medium text-gray-400 uppercase tracking-widest mb-12">No marketing expertise required</p>
              
              <div className="grid grid-cols-2 gap-8 text-left max-w-lg mx-auto border-t border-gray-100 pt-12">
                <div>
                  <h4 className="font-bold flex items-center gap-2 mb-1"><span className="text-blue-500">🔍</span> Discover</h4>
                  <p className="text-sm text-gray-500">Pages & features</p>
                </div>
                <div>
                  <h4 className="font-bold flex items-center gap-2 mb-1"><span className="text-purple-500">🧠</span> Understand</h4>
                  <p className="text-sm text-gray-500">AI product intelligence</p>
                </div>
                <div>
                  <h4 className="font-bold flex items-center gap-2 mb-1"><span className="text-pink-500">🎨</span> Create</h4>
                  <p className="text-sm text-gray-500">Images & content</p>
                </div>
                <div>
                  <h4 className="font-bold flex items-center gap-2 mb-1"><span className="text-green-500">🚀</span> Publish</h4>
                  <p className="text-sm text-gray-500">LinkedIn-ready content</p>
                </div>
              </div>

              <div className="mt-16">
                <button onClick={() => setShowAdvanced(!showAdvanced)} className="text-sm font-medium text-gray-400 hover:text-gray-600 flex items-center justify-center gap-1 mx-auto">
                  ⚙ Advanced options {showAdvanced ? '▲' : '▼'}
                </button>
                {showAdvanced && (
                  <div className="mt-4 bg-gray-50 p-4 rounded-xl inline-flex gap-4 border border-gray-100 animate-in fade-in">
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Max Pages</label>
                      <input type="number" className="w-24 p-2 bg-white border border-gray-200 rounded outline-none text-sm" value={maxPages} onChange={(e) => setMaxPages(parseInt(e.target.value))} />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Crawl Depth</label>
                      <input type="number" className="w-24 p-2 bg-white border border-gray-200 rounded outline-none text-sm" value={maxDepth} onChange={(e) => setMaxDepth(parseInt(e.target.value))} />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Timeout (sec)</label>
                      <input type="number" className="w-24 p-2 bg-white border border-gray-200 rounded outline-none text-sm" value={30} readOnly />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">AI Reasoning Model</label>
                      <select 
                        className="w-48 p-2 bg-white border border-gray-200 rounded outline-none text-sm" 
                        value={aiModel}
                        onChange={(e) => setAiModel(e.target.value)}
                      >
                        <option value="gemini-1.5-flash-latest">Gemini 1.5 Flash (Fast)</option>
                        <option value="gemini-1.5-pro-latest">Gemini 1.5 Pro (Quality)</option>
                        <option value="gemini-exp-1114">Gemini Exp 1114</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* SCREEN 2 & 3: DISCOVER */}
          {journeyStep === 'discover' && !viewingDetails && (
            <div className="max-w-2xl mx-auto mt-16 animate-in fade-in zoom-in-95 duration-500">
              {!isCompleted && !isFailed ? (
                <div className="bg-white rounded-3xl p-10 shadow-xl border border-gray-100 text-center relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gray-100">
                    <div className="h-full bg-blue-500 transition-all duration-500 ease-out" style={{ width: `${progressPercent}%` }}></div>
                  </div>
                  
                  <h2 className="text-2xl font-bold mb-1">Discovering Your Product</h2>
                  <div className="text-blue-500 font-medium mb-12 flex items-center justify-center gap-2">
                    <div className="animate-spin h-4 w-4 border-2 border-blue-500 rounded-full border-t-transparent"></div>
                    <span className="truncate max-w-xs">{crawlJob?.current_url || (product ? new URL(product.base_url).hostname : 'Connecting...')}</span>
                  </div>

                  <div className="space-y-4 text-left max-w-sm mx-auto mb-10">
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                      <span className="text-green-500">✓</span> Website connected
                    </div>
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                      <span className="text-green-500">✓</span> Pages discovered
                    </div>
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                      <span className="text-green-500">✓</span> Navigation analyzed
                    </div>
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                      {screenshots.length > 0 ? <span className="text-green-500">✓</span> : <span className="text-blue-500 animate-pulse">●</span>} 
                      Capturing screenshots
                    </div>
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-400">
                      {features.length > 0 ? <span className="text-blue-500 animate-pulse">●</span> : <span>○</span>} 
                      Extracting product evidence
                    </div>
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-400">
                      <span>○</span> Preparing product map
                    </div>
                  </div>

                  <p className="text-sm font-bold text-gray-400 uppercase tracking-widest">
                    {crawlJob?.pages_processed || 0} / {crawlJob?.max_pages || maxPages} pages
                  </p>
                </div>
              ) : isFailed ? (
                <div className="bg-white rounded-3xl p-12 shadow-xl border border-red-100 text-center">
                  <div className="w-20 h-20 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-6 text-4xl">
                    ⚠️
                  </div>
                  <h2 className="text-3xl font-extrabold mb-2 text-gray-900">Analysis Failed</h2>
                  <p className="text-gray-500 text-lg mb-10">
                    {crawlJob?.error_message || "We couldn't connect to your product website. Please check the URL and try again."}
                  </p>
                  <button 
                    onClick={() => setJourneyStep('home')}
                    className="bg-gray-900 hover:bg-gray-800 text-white font-semibold px-6 py-3 rounded-xl transition-all shadow-md w-full"
                  >
                    Try Again
                  </button>
                </div>
              ) : (
                <div className="bg-white rounded-3xl p-10 shadow-xl border border-gray-100 text-center relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gray-100">
                    <div className="h-full bg-blue-500 transition-all duration-500 ease-out" style={{ width: `100%` }}></div>
                  </div>
                  
                  <h2 className="text-2xl font-bold mb-1 text-green-600 flex items-center justify-center gap-2">
                    <span className="text-3xl">🎉</span> Product Discovery Complete
                  </h2>

                  <div className="text-green-500 font-medium mb-8 flex items-center justify-center gap-2">
                    <span className="truncate max-w-xs">We successfully mapped your product.</span>
                  </div>

                  <div className="space-y-4 text-left max-w-sm mx-auto mb-10">
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                      <span className="text-green-500">✓</span> Website connected
                    </div>
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                      <span className="text-green-500">✓</span> {pages.length} Pages discovered
                    </div>
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                      <span className="text-green-500">✓</span> Navigation analyzed
                    </div>
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                      <span className="text-green-500">✓</span> {screenshots.length} Screenshots captured
                    </div>
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                      <span className="text-green-500">✓</span> {features.length} Features extracted
                    </div>
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                      <span className="text-green-500">✓</span> Product map ready
                    </div>
                  </div>

                  <div className="pt-6 border-t border-gray-100 flex justify-center">
                    <button 
                      onClick={() => {
                        setViewingDetails(true);
                        setJourneyStep('understand');
                      }}
                      className="bg-gray-900 hover:bg-black text-white font-bold px-8 py-3 rounded-xl transition-all shadow-lg text-sm flex items-center gap-2"
                    >
                      View Product Intelligence <span className="text-lg">→</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* SCREEN 4: PRODUCT INTELLIGENCE (UNDERSTAND) */}
          {journeyStep === 'understand' && (
            <div className="max-w-4xl mx-auto mt-10 animate-in fade-in zoom-in-95 duration-500">
              <div className="text-center mb-12">
                <h2 className="text-4xl font-extrabold mb-4">Understand Your Product</h2>
                <p className="text-lg text-gray-500">AI will turn your structural product evidence into a comprehensive marketing profile.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
                <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200">
                  <h3 className="text-lg font-bold mb-4">What we will analyze:</h3>
                  <ul className="space-y-3">
                    <li className="flex items-center gap-3 text-gray-600"><span className="text-blue-500">✓</span> What your product does</li>
                    <li className="flex items-center gap-3 text-gray-600"><span className="text-blue-500">✓</span> Who it's for</li>
                    <li className="flex items-center gap-3 text-gray-600"><span className="text-blue-500">✓</span> Business problems it solves</li>
                    <li className="flex items-center gap-3 text-gray-600"><span className="text-blue-500">✓</span> Key benefits & differentiators</li>
                    <li className="flex items-center gap-3 text-gray-600"><span className="text-blue-500">✓</span> Core product modules</li>
                    <li className="flex items-center gap-3 text-gray-600"><span className="text-blue-500">✓</span> Marketing opportunities</li>
                  </ul>
                </div>
                
                <div className="bg-gradient-to-br from-indigo-50 to-blue-50 p-8 rounded-2xl shadow-inner border border-blue-100 flex flex-col justify-center items-center text-center">
                  <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-sm text-3xl mb-6">✨</div>
                  <h3 className="text-xl font-bold text-blue-900 mb-2">Ready for AI processing</h3>
                  <p className="text-blue-700 mb-8 max-w-xs">We have 41 pages of structural evidence ready to be processed by our LLM.</p>
                  
                  <button 
                    onClick={startAiAnalysis}
                    disabled={isAnalyzingAI}
                    className={`${isAnalyzingAI ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 group'} text-white font-semibold px-8 py-3 rounded-xl transition-all shadow-md w-full relative overflow-hidden`}
                  >
                    <span className="relative z-10">{isAnalyzingAI ? '✨ Analyzing (takes ~5s)...' : '✨ Analyze With AI'}</span>
                    {!isAnalyzingAI && <div className="absolute inset-0 bg-blue-500/20 w-full h-full transform -translate-x-full group-hover:translate-x-0 transition-transform duration-500"></div>}
                  </button>
                  <p className="text-xs font-bold text-blue-500 uppercase tracking-widest mt-4">Phase 2 Active</p>
                </div>
              </div>
            </div>
          )}

          {/* SCREEN 5: CREATE */}
          {journeyStep === 'create' && (
            <div className="max-w-4xl mx-auto mt-10 animate-in fade-in zoom-in-95 duration-500">
              <div className="text-center mb-12">
                <h2 className="text-4xl font-extrabold mb-4">Create Your LinkedIn Campaign</h2>
                <p className="text-lg text-gray-500">Turn your approved product intelligence into a complete LinkedIn marketing campaign.</p>
              </div>

              {/* Show AI Modules */}
              {modules.length > 0 && (
                <div className="mb-12">
                  <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <span className="text-blue-600">✨</span> Product Intelligence Profile
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {modules.map((m, i) => (
                      <div key={i} className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm hover:border-blue-300 transition-colors">
                        <h4 className="font-bold text-gray-900 mb-2">{m.name}</h4>
                        <p className="text-xs text-gray-500 mb-4 line-clamp-2">{m.description}</p>
                        <div className="space-y-2">
                          {m.features?.slice(0, 3).map((f: any, j: number) => (
                            <div key={j} className="text-xs font-medium bg-gray-50 text-gray-700 py-1.5 px-2 rounded border border-gray-100 flex items-center gap-2">
                              <span className="text-green-500">✓</span>
                              <span className="truncate">{f.name}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-3xl p-10 text-white shadow-xl mb-8 relative overflow-hidden">
                <div className="absolute top-0 right-0 -mt-10 -mr-10 opacity-20">
                  <svg width="200" height="200" viewBox="0 0 200 200" fill="none"><circle cx="100" cy="100" r="100" fill="currentColor"/></svg>
                </div>
                <div className="relative z-10 text-center">
                  <h3 className="text-3xl font-bold mb-4">✨ Create Complete LinkedIn Campaign</h3>
                  <p className="text-blue-100 mb-8 max-w-lg mx-auto text-lg">Product Page • Posts • Content</p>
                  
                  {isGeneratingCampaign ? (
                    <div className="bg-white/10 rounded-2xl p-6 text-left max-w-md mx-auto backdrop-blur-sm border border-white/20">
                      <h4 className="font-bold mb-4">Creating your campaign...</h4>
                      <ul className="space-y-3 text-sm">
                        <li className="flex items-center gap-3"><span className="text-green-300">✓</span> Understanding product positioning</li>
                        <li className="flex items-center gap-3"><span className="text-green-300 animate-pulse">●</span> Creating LinkedIn Product Page</li>
                        <li className="flex items-center gap-3 text-white/50"><span className="text-white/30">○</span> Writing launch posts</li>
                        <li className="flex items-center gap-3 text-white/50"><span className="text-white/30">○</span> Preparing campaign</li>
                      </ul>
                    </div>
                  ) : (
                    <div className="max-w-xl mx-auto bg-white/10 rounded-2xl p-6 backdrop-blur-sm border border-white/20 text-left mb-6">
                      <h4 className="font-bold mb-4">Campaign Settings</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                        <div>
                          <label className="block text-blue-200 text-xs mb-1">Target audience</label>
                          <select className="w-full bg-white/20 border border-white/10 rounded-lg p-2 text-white outline-none">
                            <option className="text-gray-900">Business Owners</option>
                            <option className="text-gray-900">Marketing Managers</option>
                            <option className="text-gray-900">Developers</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-blue-200 text-xs mb-1">Campaign goal</label>
                          <select className="w-full bg-white/20 border border-white/10 rounded-lg p-2 text-white outline-none">
                            <option className="text-gray-900">Product awareness</option>
                            <option className="text-gray-900">Lead generation</option>
                            <option className="text-gray-900">Product launch</option>
                          </select>
                        </div>
                      </div>
                      
                      <button 
                        onClick={startCampaignGeneration}
                        className="w-full bg-white text-blue-600 hover:bg-gray-50 font-bold px-8 py-4 rounded-xl transition-all shadow-lg text-lg"
                      >
                        [ Create Campaign → ]
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="text-center mb-6">
                <p className="text-gray-500 font-medium mb-2">Based on your product intelligence</p>
                <div className="flex justify-center gap-4 text-sm text-gray-600">
                  <span className="flex items-center gap-1"><span className="text-green-500">✓</span> Product profile</span>
                  <span className="flex items-center gap-1"><span className="text-green-500">✓</span> Approved features</span>
                  <span className="flex items-center gap-1"><span className="text-green-500">✓</span> Product evidence</span>
                </div>
              </div>

              <div className="mt-12">
                <h4 className="text-center text-gray-500 font-medium mb-6">Or create individually</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Product Page */}
                  <div 
                    onClick={() => product?.id && router.push(`/products/${product.id}/content/product-page`)}
                    className="bg-white p-6 rounded-2xl border border-gray-200 hover:border-blue-300 hover:shadow-md cursor-pointer group transition-all flex gap-4 items-start"
                  >
                    <div className="text-gray-700 bg-gray-50 p-3 rounded-xl group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors">
                      <BriefcaseBusiness size={28} />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-gray-900 mb-1">LinkedIn Product Page</h4>
                      <p className="text-sm text-gray-500 mb-3">Create your complete LinkedIn product listing</p>
                      <span className="text-sm font-medium text-blue-600">Create →</span>
                    </div>
                  </div>

                  {/* LinkedIn Posts */}
                  <div 
                    onClick={() => product?.id && router.push(`/products/${product.id}/content/posts`)}
                    className="bg-white p-6 rounded-2xl border border-gray-200 hover:border-blue-300 hover:shadow-md cursor-pointer group transition-all flex gap-4 items-start"
                  >
                    <div className="text-gray-700 bg-gray-50 p-3 rounded-xl group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors">
                      <PenLine size={28} />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-gray-900 mb-1">LinkedIn Posts</h4>
                      <p className="text-sm text-gray-500 mb-3">Launch posts, feature posts and educational content</p>
                      <span className="text-sm font-medium text-blue-600">Create →</span>
                    </div>
                  </div>

                  {/* Marketing Images */}
                  <div className="bg-white p-6 rounded-2xl border border-gray-200 opacity-60 cursor-not-allowed transition-all flex gap-4 items-start">
                    <div className="text-gray-500 bg-gray-50 p-3 rounded-xl">
                      <Image size={28} />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-gray-900 mb-1">Marketing Images</h4>
                      <p className="text-sm text-gray-500 mb-3">Turn product screenshots into marketing visuals</p>
                      <span className="text-sm font-medium text-gray-400">Coming soon</span>
                    </div>
                  </div>

                  {/* Product Demo Video */}
                  <div className="bg-white p-6 rounded-2xl border border-gray-200 opacity-60 cursor-not-allowed transition-all flex gap-4 items-start">
                    <div className="text-gray-500 bg-gray-50 p-3 rounded-xl">
                      <Clapperboard size={28} />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-gray-900 mb-1">Product Demo Video</h4>
                      <p className="text-sm text-gray-500 mb-3">Create a short product demonstration script</p>
                      <span className="text-sm font-medium text-gray-400">Coming soon</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* SCREEN 6: REVIEW */}
          {journeyStep === 'review' && (
            <div className="max-w-4xl mx-auto mt-10 animate-in fade-in zoom-in-95 duration-500 pb-20">
              <div className="mb-12">
                <h2 className="text-4xl font-extrabold mb-2">{product?.base_url ? new URL(product.base_url).hostname : 'StockFlow'}</h2>
                <h3 className="text-2xl text-gray-500 font-light">LinkedIn Marketing Campaign</h3>
              </div>
              
              {editingMode ? (
                <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden flex flex-col md:flex-row h-[700px] shadow-lg animate-in fade-in zoom-in-95">
                  {/* PREVIEW SIDE */}
                  <div className="md:w-1/2 bg-gray-50 p-8 border-r border-gray-200 overflow-y-auto">
                    <h3 className="font-bold text-lg text-gray-500 mb-6 uppercase tracking-wider">Preview</h3>
                    {editingMode === 'product' && (
                      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 mb-6">
                        <div className="flex gap-4 items-start mb-4">
                           <div className="w-16 h-16 bg-gray-200 rounded-lg"></div>
                           <div>
                             <h2 className="text-xl font-bold">{product?.base_url ? new URL(product.base_url).hostname : 'StockFlow'}</h2>
                             <p className="text-gray-600 font-medium">{campaignData.headline}</p>
                           </div>
                        </div>
                        <p className="text-gray-800 text-sm whitespace-pre-wrap">{campaignData.about}</p>
                      </div>
                    )}
                    
                    {editingMode === 'posts' && campaignData.posts.map((post, idx) => (
                      <div key={idx} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 mb-6">
                         <div className="flex items-center gap-3 mb-4">
                           <div className="w-10 h-10 bg-gray-300 rounded-full"></div>
                           <div>
                             <h4 className="font-bold text-sm">StockFlow</h4>
                             <p className="text-xs text-gray-500">Just now</p>
                           </div>
                         </div>
                         <p className="text-sm whitespace-pre-wrap text-gray-800 mb-4">{post}</p>
                         {mediaAssets[idx % mediaAssets.length] && (
                           <div className="rounded-lg overflow-hidden border border-gray-200">
                             <img src={`http://localhost:8000/${mediaAssets[idx % mediaAssets.length]}`} className="w-full object-cover" />
                           </div>
                         )}
                      </div>
                    ))}
                  </div>
                  
                  {/* EDITOR SIDE */}
                  <div className="md:w-1/2 flex flex-col bg-white">
                     <div className="flex justify-between items-center p-6 border-b border-gray-100">
                        <h3 className="font-bold text-xl">{editingMode === 'product' ? 'Edit Product Page' : 'Edit Launch Posts'}</h3>
                        <button onClick={async () => {
                          if (campaignId) {
                            try {
                              await fetch(`http://localhost:8000/api/campaigns/${campaignId}`, {
                                method: 'PUT',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(campaignData)
                              });
                            } catch (e) {
                              console.error("Failed to save campaign", e);
                            }
                          }
                          setEditingMode(null);
                        }} className="text-sm font-bold bg-blue-50 text-blue-600 px-4 py-2 rounded-lg hover:bg-blue-100 transition">Save & Close</button>
                     </div>
                     <div className="p-6 overflow-y-auto flex-1">
                        {editingMode === 'product' && (
                          <div className="space-y-6">
                            <div>
                              <label className="block text-sm font-bold text-gray-700 mb-2">Headline</label>
                              <input 
                                type="text" 
                                value={campaignData.headline}
                                onChange={(e) => setCampaignData({...campaignData, headline: e.target.value})}
                                className="w-full border border-gray-300 rounded-lg p-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition"
                              />
                            </div>
                            <div>
                              <label className="block text-sm font-bold text-gray-700 mb-2">About Section</label>
                              <textarea 
                                rows={6}
                                value={campaignData.about}
                                onChange={(e) => setCampaignData({...campaignData, about: e.target.value})}
                                className="w-full border border-gray-300 rounded-lg p-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition"
                              />
                            </div>
                            <div className="bg-blue-50 text-blue-800 p-4 rounded-xl text-sm mt-4">
                               <p className="font-bold flex items-center gap-2 mb-1">✨ AI Suggestion</p>
                               <p>Try making the headline shorter for better LinkedIn SEO. Click here to shorten.</p>
                            </div>
                          </div>
                        )}
                        
                        {editingMode === 'posts' && campaignData.posts.map((post, idx) => (
                          <div key={idx} className="mb-8 pb-8 border-b border-gray-100 last:border-0">
                            <div className="flex justify-between items-center mb-2">
                              <label className="block text-sm font-bold text-gray-700">Post #{idx + 1}</label>
                              <button className="text-xs text-blue-600 font-medium hover:underline flex items-center gap-1">✨ Regenerate</button>
                            </div>
                            <textarea 
                              rows={5}
                              value={post}
                              onChange={(e) => {
                                const newPosts = [...campaignData.posts];
                                newPosts[idx] = e.target.value;
                                setCampaignData({...campaignData, posts: newPosts});
                              }}
                              className="w-full border border-gray-300 rounded-lg p-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition"
                            />
                          </div>
                        ))}
                     </div>
                  </div>
                </div>
              ) : (
                <>
                  <div className="space-y-6 mb-10">
                    <div className="bg-white border-2 border-green-500 rounded-2xl p-6 shadow-sm flex items-center justify-between">
                      <div>
                        <h4 className="font-bold text-lg text-gray-900 mb-1 flex items-center gap-2"><span className="text-green-500">✓</span> LinkedIn Product Page</h4>
                        <p className="text-gray-600 text-sm">{product?.base_url ? new URL(product.base_url).hostname : 'StockFlow'}</p>
                        <p className="text-gray-500 text-sm">{campaignData.headline}</p>
                      </div>
                      <div className="flex gap-3">
                        <button onClick={() => setEditingMode('product')} className="px-6 py-2 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg text-sm font-bold transition-colors">Edit Properties</button>
                      </div>
                    </div>

                    <div className="bg-white border-2 border-green-500 rounded-2xl p-6 shadow-sm flex items-center justify-between">
                      <div>
                        <h4 className="font-bold text-lg text-gray-900 mb-1 flex items-center gap-2"><span className="text-green-500">✓</span> Launch Posts</h4>
                        <p className="text-gray-600 text-sm">{campaignData.posts.length} posts generated</p>
                      </div>
                      <button onClick={() => setEditingMode('posts')} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-bold transition-colors shadow-sm">
                        Review & Edit Posts →
                      </button>
                    </div>

                    <div className="bg-white border-2 border-green-500 rounded-2xl p-6 shadow-sm">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h4 className="font-bold text-lg text-gray-900 mb-1 flex items-center gap-2"><span className="text-green-500">✓</span> Marketing Images</h4>
                          <p className="text-gray-600 text-sm">{mediaAssets.length} assets generated</p>
                        </div>
                      </div>
                      
                      {mediaAssets.length > 0 && (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                          {mediaAssets.map((asset, i) => (
                            <div key={i} className="rounded-lg overflow-hidden border border-gray-200 bg-gray-50 aspect-video relative group">
                               <img src={`http://localhost:8000/${asset}`} className="w-full h-full object-cover" alt="Marketing Asset" />
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex justify-center">
                    <button 
                      onClick={() => setJourneyStep('publish')}
                      className="bg-gray-900 hover:bg-black text-white font-bold px-10 py-4 rounded-xl transition-all shadow-xl text-lg flex items-center gap-3"
                    >
                      Approve Campaign →
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

          {/* SCREEN 7: PUBLISH */}
          {journeyStep === 'publish' && (
            <div className="max-w-3xl mx-auto mt-20 text-center animate-in fade-in zoom-in-95 duration-500">
              <div className="w-24 h-24 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6 text-5xl">
                🚀
              </div>
              <h2 className="text-4xl font-extrabold mb-4">Your Marketing Kit Is Ready</h2>
              <p className="text-xl text-gray-500 mb-12">The StockFlow LinkedIn campaign has been generated and approved.</p>
              
              <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-200 mb-12 flex justify-center gap-12 text-left">
                <ul className="space-y-4">
                  <li className="flex items-center gap-3 text-gray-900 font-medium"><span className="text-green-500 bg-green-50 rounded-full p-1">✓</span> Product Page</li>
                  <li className="flex items-center gap-3 text-gray-900 font-medium"><span className="text-green-500 bg-green-50 rounded-full p-1">✓</span> 10 LinkedIn Posts</li>
                  <li className="flex items-center gap-3 text-gray-900 font-medium"><span className="text-green-500 bg-green-50 rounded-full p-1">✓</span> 5 Feature Images</li>
                </ul>
                <ul className="space-y-4">
                  <li className="flex items-center gap-3 text-gray-900 font-medium"><span className="text-green-500 bg-green-50 rounded-full p-1">✓</span> 1 Carousel</li>
                  <li className="flex items-center gap-3 text-gray-900 font-medium"><span className="text-green-500 bg-green-50 rounded-full p-1">✓</span> 1 Demo Script</li>
                </ul>
              </div>

              <div className="flex flex-col sm:flex-row justify-center gap-4">
                <a 
                  href={`http://localhost:8000/api/products/${product?.id}/export`}
                  download
                  className="bg-white text-gray-900 border border-gray-300 hover:bg-gray-50 font-semibold px-8 py-4 rounded-xl transition-all shadow-sm flex items-center justify-center gap-2"
                >
                  <span className="text-xl">📦</span> Export ZIP
                </a>
                <button 
                  onClick={handleLinkedInPublish}
                  disabled={publishStatus === 'publishing'}
                  className={`${isLinkedInAuth ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-800 hover:bg-gray-900'} text-white font-semibold px-8 py-4 rounded-xl transition-all shadow-md flex items-center justify-center gap-2 ${publishStatus === 'publishing' && 'opacity-70 cursor-not-allowed'}`}
                >
                  {publishStatus === 'publishing' ? (
                    'Publishing...'
                  ) : !isLinkedInAuth ? (
                    <><span className="text-xl font-serif font-bold">in</span> Connect LinkedIn</>
                  ) : (
                    <><span className="text-xl font-serif font-bold">in</span> Confirm Publish</>
                  )}
                </button>
              </div>
              
              {publishStatus === 'published' && (
                <div className="mt-8 bg-green-50 border border-green-200 text-green-700 p-4 rounded-xl inline-flex items-center gap-2">
                  <span>✅ Campaign published successfully!</span>
                  <a href={postUrl} target="_blank" className="font-bold underline hover:text-green-800">View on LinkedIn →</a>
                </div>
              )}
              
              <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mt-6">Phase 6: LinkedIn Publishing Engine</p>
            </div>
          )}


          {/* TECHNICAL DETAILS DASHBOARD (VIEWING DETAILS FROM DISCOVER STEP) */}
          {journeyStep === 'discover' && viewingDetails && isCompleted && (
            <div className="absolute inset-0 bg-[#F8FAFC] z-20 flex flex-col animate-in slide-in-from-bottom-8 duration-500">
              
              <div className="bg-white border-b border-gray-200 px-8 py-4 flex justify-between items-center shrink-0">
                <div className="flex items-center gap-4">
                  <button onClick={() => setViewingDetails(false)} className="text-sm font-medium text-gray-500 hover:text-gray-900">← Back to Journey</button>
                  <div className="h-4 w-px bg-gray-300"></div>
                  <h2 className="font-bold text-gray-900">Product Analysis</h2>
                  <span className="text-sm text-gray-500">{product?.base_url}</span>
                </div>
                <button onClick={exportJSON} className="text-sm border border-gray-300 hover:bg-gray-50 px-4 py-2 rounded-lg font-medium transition-colors">
                  Export Data
                </button>
              </div>

              <div className="px-8 pt-6 border-b border-gray-200 bg-white shrink-0">
                <nav className="-mb-px flex space-x-8">
                  {['overview', 'pages', 'features', 'screenshots', 'evidence'].map(tab => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm capitalize transition-colors ${
                        activeTab === tab 
                          ? 'border-blue-600 text-blue-600' 
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </nav>
              </div>

              <div className="flex-1 overflow-y-auto p-8">
                {/* TAB: OVERVIEW */}
                {activeTab === 'overview' && (
                  <div className="space-y-8 animate-in fade-in">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                        <div className="text-4xl font-bold text-gray-900 mb-1">{pages.length}</div>
                        <div className="text-sm text-gray-500 font-medium">Pages analyzed</div>
                      </div>
                      <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                        <div className="text-4xl font-bold text-gray-900 mb-1">{screenshots.length}</div>
                        <div className="text-sm text-gray-500 font-medium">Screenshots captured</div>
                      </div>
                      <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                        <div className="text-4xl font-bold text-gray-900 mb-1">{features.length}</div>
                        <div className="text-sm text-gray-500 font-medium">Features discovered</div>
                      </div>
                      <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                        <div className="text-4xl font-bold text-gray-900 mb-1">{crawlJob?.failed_pages || 0}</div>
                        <div className="text-sm text-gray-500 font-medium">Crawl errors</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* TAB: PAGES */}
                {activeTab === 'pages' && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden animate-in fade-in flex flex-col h-full">
                    <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center shrink-0">
                      <input 
                        type="text" 
                        placeholder="Search pages..." 
                        className="px-4 py-2 border border-gray-200 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={pageSearch}
                        onChange={e => setPageSearch(e.target.value)}
                      />
                      <div className="text-sm text-gray-500 font-medium">{filteredPages.length} pages found</div>
                    </div>
                    <div className="overflow-x-auto overflow-y-auto flex-1">
                      <table className="w-full text-left text-sm whitespace-nowrap">
                        <thead className="bg-white sticky top-0 border-b border-gray-100 text-xs uppercase tracking-wider text-gray-500 z-10">
                          <tr>
                            <th className="px-6 py-4 font-semibold">URL Path</th>
                            <th className="px-6 py-4 font-semibold">Title</th>
                            <th className="px-6 py-4 font-semibold">Status</th>
                            <th className="px-6 py-4 font-semibold text-right">Depth</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                          {filteredPages.map(page => {
                            const path = new URL(page.url).pathname;
                            return (
                              <tr key={page.id} className="hover:bg-gray-50 transition-colors">
                                <td className="px-6 py-4 font-medium text-gray-900 truncate max-w-[200px]" title={path}>{path === '/' ? '/ (Home)' : path}</td>
                                <td className="px-6 py-4 text-gray-500 truncate max-w-[300px]" title={page.title}>{page.title || '-'}</td>
                                <td className="px-6 py-4">
                                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${page.status === 200 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                    {page.status}
                                  </span>
                                </td>
                                <td className="px-6 py-4 text-gray-500 text-right">{page.depth}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* TAB: FEATURES */}
                {activeTab === 'features' && (
                  <div className="animate-in fade-in">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {features.map(f => (
                        <div key={f.id} className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
                          <h4 className="font-bold text-gray-900 mb-1">{f.name}</h4>
                          <span className="text-[10px] uppercase font-bold tracking-wider text-gray-400">Discovered</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* TAB: SCREENSHOTS */}
                {activeTab === 'screenshots' && (
                  <div className="animate-in fade-in">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                      {screenshots.map(s => {
                        const relatedPage = pages.find(p => p.id === s.page_id);
                        const displayTitle = relatedPage?.title || 'Unknown Page';
                        const path = relatedPage ? new URL(relatedPage.url).pathname : '';
                        return (
                          <div key={s.id} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden group">
                            <div 
                              className="aspect-video bg-gray-100 relative overflow-hidden border-b border-gray-100 cursor-pointer"
                              onClick={() => setPreviewImage(`http://localhost:8000/${s.image_path}`)}
                            >
                              <div className="absolute inset-0 flex items-center justify-center text-gray-400">
                                 <img src={`http://localhost:8000/${s.image_path}`} alt="screenshot" className="object-cover w-full h-full hover:scale-105 transition-transform duration-500" onError={(e) => { e.currentTarget.style.display='none' }} />
                              </div>
                            </div>
                            <div className="p-4">
                              <h4 className="font-bold text-gray-900 truncate text-sm" title={displayTitle}>{displayTitle}</h4>
                              <p className="text-xs text-gray-500 mt-1 truncate">{path}</p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* TAB: EVIDENCE */}
                {activeTab === 'evidence' && (
                  <div className="space-y-4 animate-in fade-in pb-12">
                    <p className="text-sm text-gray-500 mb-6 font-medium">Raw structural data captured by the crawler before AI processing.</p>
                    {pages.map(page => (
                      <details key={page.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden group">
                        <summary className="p-4 font-mono text-xs text-gray-700 cursor-pointer bg-gray-50 group-hover:bg-gray-100 transition-colors list-none flex justify-between border-b border-gray-100">
                          <span className="truncate pr-4">{page.url}</span>
                          <span className="text-gray-400 shrink-0">Status: {page.status} | Depth: {page.depth} ▼</span>
                        </summary>
                        <div className="p-6 text-sm text-gray-700 bg-white">
                          <div className="grid grid-cols-1 gap-4">
                            <div><strong className="block text-[10px] text-gray-400 uppercase tracking-widest mb-1">Title</strong><div className="font-medium">{page.title || '-'}</div></div>
                            <div><strong className="block text-[10px] text-gray-400 uppercase tracking-widest mb-1">H1 Tags (Candidate Features)</strong><pre className="mt-1 bg-gray-50 p-3 rounded-lg border border-gray-100 text-xs overflow-x-auto font-mono text-gray-800">{page.h1 || '[]'}</pre></div>
                            <div><strong className="block text-[10px] text-gray-400 uppercase tracking-widest mb-1">H2 Tags</strong><pre className="mt-1 bg-gray-50 p-3 rounded-lg border border-gray-100 text-xs overflow-x-auto font-mono text-gray-800">{page.h2 || '[]'}</pre></div>
                          </div>
                        </div>
                      </details>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

        </main>
      </div>

      {/* Image Preview Modal */}
      {previewImage && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4 backdrop-blur-sm" onClick={() => setPreviewImage(null)}>
          <img src={previewImage} className="max-w-full max-h-full rounded-xl shadow-2xl ring-1 ring-white/10" />
        </div>
      )}

    </div>
  );
}
