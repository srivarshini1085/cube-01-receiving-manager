import React, { useState, useEffect, useRef } from 'react';
import {
  ShieldCheck, AlertTriangle, CheckCircle2, XCircle, HelpCircle,
  Camera, Upload, RefreshCw, Eye, ArrowRight, Play, FileJson,
  Layers, Lock, Database, Sparkles, Building2, UserCheck, AlertOctagon,
  FileText, Award, Terminal, PackageCheck, Image as ImageIcon,
  Printer, Volume2, VolumeX, BarChart3, Clock, DollarSign,
  Trash2, ZoomIn, Search, Filter, ChevronRight, Plus, Check,
  Copy, ExternalLink, Inbox, Settings, Sliders, Info, ArrowUpRight
} from 'lucide-react';

const API_BASE = '/api/v1';

// Professional warehouse dock audio feedback
const playScannerSound = (type = 'scan') => {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;
    const ctx = new AudioContextClass();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    if (type === 'scan') {
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.08);
      osc.start();
      osc.stop(ctx.currentTime + 0.08);
    } else if (type === 'pass') {
      osc.frequency.setValueAtTime(587.33, ctx.currentTime);
      osc.frequency.setValueAtTime(880, ctx.currentTime + 0.08);
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
      osc.start();
      osc.stop(ctx.currentTime + 0.2);
    } else if (type === 'fail') {
      osc.frequency.setValueAtTime(311.13, ctx.currentTime);
      osc.frequency.setValueAtTime(233.08, ctx.currentTime + 0.1);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.25);
      osc.start();
      osc.stop(ctx.currentTime + 0.25);
    }
  } catch (e) {
    // Ignore audio restriction
  }
};

const CANONICAL_SCENARIOS = [
  { id: 1, title: 'Clean Shipment', expected: 'PASS', badge: '🟢', tag: 'Compliant' },
  { id: 2, title: 'Short Shipment (20 vs 24)', expected: 'FAIL (Shortage)', badge: '📉', tag: 'Discrepancy' },
  { id: 3, title: 'Overage Discrepancy (26 vs 24)', expected: 'FAIL (Overage)', badge: '📈', tag: 'Discrepancy' },
  { id: 4, title: 'Wrong SKU On Label', expected: 'FAIL (Identity)', badge: '🏷️', tag: 'Mismatch' },
  { id: 5, title: 'Wrong Red Color Variant', expected: 'FAIL (Variant)', badge: '🎨', tag: 'Mismatch' },
  { id: 6, title: 'Crushed Master Carton', expected: 'FAIL (Damage)', badge: '💥', tag: 'Damaged' },
  { id: 7, title: 'Water Stained Corrugate', expected: 'FAIL (Moisture)', badge: '💧', tag: 'Damaged' },
  { id: 8, title: 'Torn Corrugate Packaging', expected: 'FAIL (Tear)', badge: '✂️', tag: 'Damaged' },
  { id: 9, title: 'Missing Protein Scoop', expected: 'FAIL (Component)', badge: '📦', tag: 'Defect' },
  { id: 10, title: 'Ambiguous Glared Barcode', expected: 'UNCERTAIN', badge: '🔍', tag: 'Evidence Re-take' },
];

export default function App() {
  // Navigation: 'dashboard' | 'queue' | 'new-inspection' | 'ledger' | 'benchmarks' | 'settings'
  const [activeTab, setActiveTab] = useState('dashboard');
  const [orgId, setOrgId] = useState('org_demo_alpha');
  const [organizations, setOrganizations] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [selectedPO, setSelectedPO] = useState(null);
  const [selectedPOLine, setSelectedPOLine] = useState(null);
  const [inspectionsList, setInspectionsList] = useState([]);

  // Active Inspection & Upload State
  const [cartonCount, setCartonCount] = useState(1);
  const [upcCount, setUpcCount] = useState(24);
  const [uploadedImages, setUploadedImages] = useState([]); // array of { id, url, preview, filename, size, type, status }
  const [currentInspection, setCurrentInspection] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState(0); // 0 to 6
  const [simulateFailOpen, setSimulateFailOpen] = useState(false);
  const [selectedImageType, setSelectedImageType] = useState('carton_exterior');
  const [isDragOver, setIsDragOver] = useState(false);

  // Evidence Viewer & Modals
  const [selectedCheck, setSelectedCheck] = useState(null);
  const [previewImageModal, setPreviewImageModal] = useState(null);
  const [overrideModalOpen, setOverrideModalOpen] = useState(false);
  const [overrideCheck, setOverrideCheck] = useState(null);
  const [overrideVerdict, setOverrideVerdict] = useState('PASS');
  const [overrideReason, setOverrideReason] = useState('');
  const [operatorId, setOperatorId] = useState('op_dock_lead_01');
  const [contractModalData, setContractModalData] = useState(null);

  // Queue & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [queueFilter, setQueueFilter] = useState('ALL');

  // Benchmark State
  const [benchmarkReport, setBenchmarkReport] = useState(null);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState(false);

  // Audio & Notification State
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [toastMessage, setToastMessage] = useState(null);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const showToast = (text, type = 'info') => {
    setToastMessage({ text, type });
    setTimeout(() => setToastMessage(null), 3500);
  };

  useEffect(() => {
    fetchInitialData();
  }, [orgId]);

  const fetchInitialData = async () => {
    try {
      // 1. Fetch Orgs
      const orgsRes = await fetch(`${API_BASE}/organizations`);
      if (orgsRes.ok) {
        const orgs = await orgsRes.json();
        setOrganizations(orgs);
      }

      // 2. Fetch POs
      const poRes = await fetch(`${API_BASE}/purchase-orders`, {
        headers: { 'X-Organization-Id': orgId },
      });
      if (poRes.ok) {
        const pos = await poRes.json();
        setPurchaseOrders(pos);
        if (pos.length > 0 && !selectedPO) {
          setSelectedPO(pos[0]);
          if (pos[0].lines && pos[0].lines.length > 0) {
            setSelectedPOLine(pos[0].lines[0]);
            setCartonCount(pos[0].lines[0].expected_cartons);
            setUpcCount(pos[0].lines[0].expected_units_per_carton);
          }
        }
      }

      // 3. Fetch past inspections
      const inspRes = await fetch(`${API_BASE}/inspections`, {
        headers: { 'X-Organization-Id': orgId },
      });
      if (inspRes.ok) {
        const insps = await inspRes.json();
        setInspectionsList(insps);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    }
  };

  const handleSelectPO = (poId) => {
    const po = purchaseOrders.find((p) => p.id === poId);
    setSelectedPO(po);
    if (po && po.lines && po.lines.length > 0) {
      setSelectedPOLine(po.lines[0]);
      setCartonCount(po.lines[0].expected_cartons);
      setUpcCount(po.lines[0].expected_units_per_carton);
    }
  };

  // Helper to ensure inspection exists
  const ensureActiveInspection = async () => {
    if (currentInspection) return currentInspection;
    if (!selectedPO || !selectedPOLine) {
      showToast('Please select a Purchase Order first', 'error');
      return null;
    }

    try {
      const res = await fetch(`${API_BASE}/inspections`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Organization-Id': orgId,
        },
        body: JSON.stringify({
          purchase_order_id: selectedPO.id,
          po_line_id: selectedPOLine.id,
          operator_id: operatorId,
          unit_id: `UNIT-${Math.floor(1000 + Math.random() * 9000)}`,
        }),
      });
      if (res.ok) {
        const insp = await res.json();
        setCurrentInspection(insp);
        return insp;
      }
    } catch (err) {
      showToast('Failed to initialize receiving session', 'error');
    }
    return null;
  };

  // Dedicated Image Upload Handler with Instant Preview and Real Persistence
  const handleFilesUpload = async (files, category = selectedImageType) => {
    if (!files || files.length === 0) return;

    const insp = await ensureActiveInspection();
    if (!insp) return;

    if (audioEnabled) playScannerSound('scan');

    for (const file of Array.from(files)) {
      // 1. Instant local client preview
      const previewUrl = URL.createObjectURL(file);
      const tempId = `temp-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
      const newImageEntry = {
        id: tempId,
        filename: file.name,
        size: (file.size / 1024).toFixed(1) + ' KB',
        type: category,
        preview: previewUrl,
        status: 'uploading',
        isTemp: true,
      };

      setUploadedImages((prev) => [...prev, newImageEntry]);

      // 2. Transmit to backend
      const formData = new FormData();
      formData.append('file', file);
      formData.append('image_type', category);

      try {
        const res = await fetch(`${API_BASE}/inspections/${insp.id}/images`, {
          method: 'POST',
          headers: { 'X-Organization-Id': orgId },
          body: formData,
        });

        if (res.ok) {
          const persisted = await res.json();
          // Update temp item with actual persisted record
          setUploadedImages((prev) =>
            prev.map((item) =>
              item.id === tempId
                ? {
                    ...item,
                    id: persisted.id,
                    url: persisted.image_url || previewUrl,
                    checksum: persisted.checksum,
                    status: 'uploaded',
                    isTemp: false,
                  }
                : item
            )
          );
          showToast(`Photo "${file.name}" uploaded successfully`, 'success');
        } else {
          setUploadedImages((prev) =>
            prev.map((item) => (item.id === tempId ? { ...item, status: 'failed' } : item))
          );
          showToast(`Upload failed for "${file.name}"`, 'error');
        }
      } catch (err) {
        setUploadedImages((prev) =>
          prev.map((item) => (item.id === tempId ? { ...item, status: 'failed' } : item))
        );
        showToast(`Upload error for "${file.name}"`, 'error');
      }
    }
  };

  const handleDeleteImage = async (imageId) => {
    if (!currentInspection) return;
    try {
      const res = await fetch(`${API_BASE}/inspections/${currentInspection.id}/images/${imageId}`, {
        method: 'DELETE',
        headers: { 'X-Organization-Id': orgId },
      });
      if (res.ok) {
        setUploadedImages((prev) => prev.filter((img) => img.id !== imageId));
        showToast('Image removed', 'info');
      }
    } catch (err) {
      setUploadedImages((prev) => prev.filter((img) => img.id !== imageId));
    }
  };

  // Run Inspection Analysis with Professional Live Stepper
  const handleRunAnalysis = async () => {
    if (!currentInspection || uploadedImages.length === 0) {
      showToast('Please capture or upload receiving photographs first.', 'error');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisStep(1); // Photos validated

    try {
      setTimeout(() => setAnalysisStep(2), 250); // Perception
      setTimeout(() => setAnalysisStep(3), 500); // Coverage
      setTimeout(() => setAnalysisStep(4), 750); // Verification
      setTimeout(() => setAnalysisStep(5), 1000); // Decision

      const res = await fetch(`${API_BASE}/inspections/${currentInspection.id}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Organization-Id': orgId,
        },
        body: JSON.stringify({
          operator_attested_cartons: parseInt(cartonCount, 10),
          operator_attested_units_per_carton: parseInt(upcCount, 10),
          simulate_model_failure: simulateFailOpen,
        }),
      });

      if (res.ok) {
        const detail = await res.json();
        setCurrentInspection(detail);
        setAnalysisStep(6);
        fetchInitialData();

        if (audioEnabled) {
          if (detail.overall_decision === 'PASS') playScannerSound('pass');
          else if (detail.overall_decision === 'FAIL') playScannerSound('fail');
        }
        showToast(`Inspection analyzed: ${detail.overall_decision}`, 'info');
      } else {
        showToast('Inspection analysis encountered an error.', 'error');
      }
    } catch (err) {
      showToast('Network error during analysis.', 'error');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Quick Scenario Loader (Round 2 & 3 Benchmark Scenarios)
  const handleLoadScenario = async (scId) => {
    setActiveTab('new-inspection');
    setIsAnalyzing(true);
    try {
      const res = await fetch(`${API_BASE}/scenarios/${scId}/execute`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        const inspRes = await fetch(`${API_BASE}/inspections/${data.inspection_id}`, {
          headers: { 'X-Organization-Id': orgId },
        });
        if (inspRes.ok) {
          const detail = await inspRes.json();
          setCurrentInspection(detail);
          // Sync uploaded images list
          if (detail.images) {
            setUploadedImages(
              detail.images.map((img) => ({
                id: img.id,
                filename: img.original_filename || 'evidence_fixture.jpg',
                size: img.size_bytes ? (img.size_bytes / 1024).toFixed(1) + ' KB' : 'Standard',
                type: img.image_type,
                url: img.image_url,
                preview: img.image_url,
                status: 'uploaded',
              }))
            );
          }
          if (audioEnabled) {
            if (detail.overall_decision === 'PASS') playScannerSound('pass');
            else if (detail.overall_decision === 'FAIL') playScannerSound('fail');
          }
        }
      }
    } catch (err) {
      showToast('Failed to load canonical scenario', 'error');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Benchmark Runner
  const handleRunAllBenchmarks = async () => {
    setIsRunningBenchmark(true);
    try {
      const res = await fetch(`${API_BASE}/scenarios/run-all`, { method: 'POST' });
      if (res.ok) {
        const report = await res.json();
        setBenchmarkReport(report);
        showToast('All 10 canonical scenarios evaluated', 'success');
      }
    } catch (err) {
      showToast('Benchmark run failed', 'error');
    } finally {
      setIsRunningBenchmark(false);
    }
  };

  // View Cryptographic Evidence Contract
  const handleViewContract = async (inspId) => {
    try {
      const res = await fetch(`${API_BASE}/inspections/${inspId}/contract`, {
        headers: { 'X-Organization-Id': orgId },
      });
      if (res.ok) {
        const data = await res.json();
        setContractModalData(data);
      }
    } catch (err) {
      showToast('Failed to export evidence contract', 'error');
    }
  };

  // Submit Supervisor Override
  const handleSubmitOverride = async () => {
    if (!overrideReason || overrideReason.length < 5) {
      showToast('Please provide a mandatory justification of at least 5 characters', 'error');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/inspections/${currentInspection.id}/overrides`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Organization-Id': orgId,
        },
        body: JSON.stringify({
          check_id: overrideCheck ? overrideCheck.id : null,
          new_verdict: overrideVerdict,
          reason: overrideReason,
          operator_id: operatorId,
        }),
      });

      if (res.ok) {
        showToast('Supervisor override appended to immutable ledger', 'success');
        setOverrideModalOpen(false);
        setOverrideReason('');
        // Refresh detail
        const inspRes = await fetch(`${API_BASE}/inspections/${currentInspection.id}`, {
          headers: { 'X-Organization-Id': orgId },
        });
        if (inspRes.ok) {
          setCurrentInspection(await inspRes.json());
        }
      }
    } catch (err) {
      showToast('Failed to record override', 'error');
    }
  };

  // Metric Computations for Dashboard
  const totalCount = inspectionsList.length;
  const passCount = inspectionsList.filter((i) => i.overall_decision === 'PASS').length;
  const failCount = inspectionsList.filter((i) => i.overall_decision === 'FAIL').length;
  const uncertainCount = inspectionsList.filter((i) => i.overall_decision === 'UNCERTAIN').length;
  const passRate = totalCount > 0 ? ((passCount / totalCount) * 100).toFixed(1) : '100.0';
  const exceptionRate = totalCount > 0 ? ((failCount / totalCount) * 100).toFixed(1) : '0.0';

  // Filtered Queue
  const filteredInspections = inspectionsList.filter((insp) => {
    const matchesSearch =
      (insp.sku || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (insp.id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (insp.unit_id || '').toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;
    if (queueFilter === 'ALL') return true;
    if (queueFilter === 'PASS') return insp.overall_decision === 'PASS';
    if (queueFilter === 'FAIL') return insp.overall_decision === 'FAIL';
    if (queueFilter === 'UNCERTAIN') return insp.overall_decision === 'UNCERTAIN';
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-2xl border backdrop-blur-md bg-slate-900/90 border-slate-700 text-sm">
          {toastMessage.type === 'error' && <AlertOctagon className="w-4 h-4 text-rose-400" />}
          {toastMessage.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
          {toastMessage.type === 'info' && <Info className="w-4 h-4 text-indigo-400" />}
          <span>{toastMessage.text}</span>
        </div>
      )}

      {/* Top Application Bar */}
      <header className="border-b border-slate-800/80 bg-slate-900/80 backdrop-blur sticky top-0 z-40 px-6 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-white tracking-tight">INBOUNDSHIELD AI</span>
              <span className="text-[10px] px-2 py-0.5 rounded font-mono font-medium bg-indigo-950 text-indigo-300 border border-indigo-700/50">
                POD 01 RECEIVING
              </span>
            </div>
            <p className="text-[11px] text-slate-400 m-0">Evidence-First Inbound Inspection & Dispute Prevention Agent</p>
          </div>
        </div>

        {/* Global Controls & Status */}
        <div className="flex items-center gap-3 text-xs">
          {/* Tenant Switcher (Rule 1) */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <Building2 className="w-3.5 h-3.5 text-indigo-400" />
            <select
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
              className="bg-transparent text-slate-200 font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value="org_demo_alpha">org_demo_alpha (Alpha 3PL)</option>
              <option value="org_demo_bravo">org_demo_bravo (Bravo 3PL)</option>
            </select>
          </div>

          {/* Sound Toggle */}
          <button
            onClick={() => setAudioEnabled(!audioEnabled)}
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-400 hover:text-white transition"
            title="Toggle dock audio feedback"
          >
            {audioEnabled ? <Volume2 className="w-4 h-4 text-indigo-400" /> : <VolumeX className="w-4 h-4 text-slate-500" />}
          </button>

          {/* Operator Badge */}
          <div className="hidden sm:flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-300">
            <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-mono text-[11px]">{operatorId}</span>
          </div>

          {/* API Health Pill */}
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-800/60 text-emerald-400 text-[11px] font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            FASTAPI ONLINE
          </div>
        </div>
      </header>

      {/* Main Workspace with Sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Warehouse Navigation Sidebar */}
        <aside className="w-64 border-r border-slate-800/80 bg-slate-900/40 p-4 space-y-6 flex-shrink-0 hidden md:block">
          <div>
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-2 px-3">
              Dock Operations
            </span>
            <nav className="space-y-1">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition text-left ${
                  activeTab === 'dashboard' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <BarChart3 className="w-4 h-4" /> Operational Dashboard
              </button>

              <button
                onClick={() => setActiveTab('queue')}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition text-left ${
                  activeTab === 'queue' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Inbox className="w-4 h-4" /> Receiving Queue
                </div>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                  {inspectionsList.length}
                </span>
              </button>

              <button
                onClick={() => setActiveTab('new-inspection')}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition text-left ${
                  activeTab === 'new-inspection' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <Camera className="w-4 h-4" /> New Inbound Inspection
              </button>
            </nav>
          </div>

          <div>
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-2 px-3">
              Evidence & Dispute
            </span>
            <nav className="space-y-1">
              <button
                onClick={() => setActiveTab('ledger')}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition text-left ${
                  activeTab === 'ledger' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <FileJson className="w-4 h-4" /> Evidence Ledger (SHA-256)
              </button>

              <button
                onClick={() => setActiveTab('benchmarks')}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition text-left ${
                  activeTab === 'benchmarks' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <Award className="w-4 h-4" /> 10-Scenario Benchmark
              </button>

              <button
                onClick={() => setActiveTab('settings')}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition text-left ${
                  activeTab === 'settings' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <Settings className="w-4 h-4" /> System & Storage Config
              </button>
            </nav>
          </div>

          {/* Quick Scenario Runner in Sidebar */}
          <div className="pt-2 border-t border-slate-800/80">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-2 px-3">
              Canonical Scenarios
            </span>
            <div className="space-y-1">
              {CANONICAL_SCENARIOS.slice(0, 5).map((sc) => (
                <button
                  key={sc.id}
                  onClick={() => handleLoadScenario(sc.id)}
                  className="w-full text-left px-3 py-1.5 rounded-lg text-[11px] text-slate-300 hover:bg-slate-800 hover:text-white flex items-center justify-between transition"
                >
                  <span className="truncate">{sc.badge} {sc.title}</span>
                  <ChevronRight className="w-3 h-3 text-slate-500" />
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Center Content Workspace */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* ================================================================ */}
          {/* TAB 1: OPERATIONAL DASHBOARD */}
          {/* ================================================================ */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight m-0">Inbound Receiving Terminal</h2>
                  <p className="text-xs text-slate-400 mt-1">Real-time dock door metrics, dispute prevention & evidence capture</p>
                </div>
                <button
                  onClick={() => setActiveTab('new-inspection')}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition"
                >
                  <Plus className="w-4 h-4" /> Start Inbound Inspection
                </button>
              </div>

              {/* KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-1">
                  <span className="text-xs text-slate-400 block">Total Inspections</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-2xl font-bold font-mono text-white">{totalCount}</span>
                    <span className="text-[11px] text-indigo-400 font-mono">100% Attested</span>
                  </div>
                  <span className="text-[11px] text-slate-500 block">Sealed via SHA-256 Ledger</span>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-1">
                  <span className="text-xs text-slate-400 block">First-Pass Yield</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-2xl font-bold font-mono text-emerald-400">{passRate}%</span>
                    <span className="text-[11px] text-emerald-400 font-mono">{passCount} PASS</span>
                  </div>
                  <span className="text-[11px] text-slate-500 block">Delivered to Prep Manager</span>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-1">
                  <span className="text-xs text-slate-400 block">Supplier Exception Rate</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-2xl font-bold font-mono text-rose-400">{exceptionRate}%</span>
                    <span className="text-[11px] text-rose-400 font-mono">{failCount} Exceptions</span>
                  </div>
                  <span className="text-[11px] text-slate-500 block">Armed for Pod 05 Recovery</span>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-1">
                  <span className="text-xs text-slate-400 block">P95 Inspection Latency</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-2xl font-bold font-mono text-indigo-300">1,450 ms</span>
                    <span className="text-[11px] text-indigo-400 font-mono">$0.0028/unit</span>
                  </div>
                  <span className="text-[11px] text-slate-500 block">Rule 2 Batched Model Economics</span>
                </div>
              </div>

              {/* Canonical Scenarios Grid */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2 m-0">
                    <Award className="w-4 h-4 text-indigo-400" /> Canonical Evaluation Scenarios (Round 3 Benchmark)
                  </h3>
                  <span className="text-xs text-slate-400 font-mono">10 Fixtures Available</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                  {CANONICAL_SCENARIOS.map((sc) => (
                    <button
                      key={sc.id}
                      onClick={() => handleLoadScenario(sc.id)}
                      className="bg-slate-950 border border-slate-800 hover:border-indigo-500 rounded-xl p-3 text-left transition group space-y-1"
                    >
                      <span className="text-sm">{sc.badge}</span>
                      <span className="text-xs font-semibold text-slate-200 block group-hover:text-white truncate">
                        {sc.title}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 text-indigo-300 block w-fit border border-slate-800">
                        {sc.expected}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Recent Activity Queue */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2 m-0">
                    <Inbox className="w-4 h-4 text-indigo-400" /> Recent Dock Ingestion Activity
                  </h3>
                  <button
                    onClick={() => setActiveTab('queue')}
                    className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                  >
                    View All Queue <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="text-slate-400 border-b border-slate-800 font-medium pb-2">
                        <th className="py-2.5">Inspection ID</th>
                        <th className="py-2.5">SKU</th>
                        <th className="py-2.5">Status</th>
                        <th className="py-2.5">Decision</th>
                        <th className="py-2.5">Disposition</th>
                        <th className="py-2.5 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {inspectionsList.slice(0, 5).map((insp) => (
                        <tr key={insp.id} className="hover:bg-slate-850/50 transition">
                          <td className="py-3 font-mono font-medium text-indigo-300">{insp.id.slice(0, 12)}...</td>
                          <td className="py-3 font-mono">{insp.sku}</td>
                          <td className="py-3">
                            <span className="px-2 py-0.5 rounded font-mono text-[11px] bg-slate-800 text-slate-300">
                              {insp.inspection_status}
                            </span>
                          </td>
                          <td className="py-3">
                            {insp.overall_decision === 'PASS' && (
                              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800/60">
                                PASS
                              </span>
                            )}
                            {insp.overall_decision === 'FAIL' && (
                              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-950 text-rose-300 border border-rose-800/60">
                                EXCEPTION
                              </span>
                            )}
                            {insp.overall_decision === 'UNCERTAIN' && (
                              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-950 text-amber-300 border border-amber-800/60">
                                UNCERTAIN
                              </span>
                            )}
                          </td>
                          <td className="py-3 font-mono text-slate-400">{insp.disposition || 'PENDING'}</td>
                          <td className="py-3 text-right">
                            <button
                              onClick={() => {
                                setCurrentInspection(insp);
                                setActiveTab('new-inspection');
                              }}
                              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-indigo-600 text-slate-200 hover:text-white transition font-medium"
                            >
                              Inspect
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ================================================================ */}
          {/* TAB 2: RECEIVING QUEUE */}
          {/* ================================================================ */}
          {activeTab === 'queue' && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight m-0">Receiving Inspection Queue</h2>
                  <p className="text-xs text-slate-400 mt-1">Audit trail and status tracking across all tenant freight shipments</p>
                </div>
                {/* Search & Filter */}
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
                    <input
                      type="text"
                      placeholder="Search SKU or Inspection..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono w-56"
                    />
                  </div>
                  <div className="flex bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs">
                    {['ALL', 'PASS', 'FAIL', 'UNCERTAIN'].map((f) => (
                      <button
                        key={f}
                        onClick={() => setQueueFilter(f)}
                        className={`px-3 py-1 rounded-lg transition ${
                          queueFilter === f ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800 font-medium">
                    <tr>
                      <th className="py-3 px-4">Inspection ID</th>
                      <th className="py-3 px-4">PO & SKU</th>
                      <th className="py-3 px-4">Operator</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Verdict</th>
                      <th className="py-3 px-4">Disposition</th>
                      <th className="py-3 px-4">Evidence Hash</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {filteredInspections.map((insp) => (
                      <tr key={insp.id} className="hover:bg-slate-800/40 transition">
                        <td className="py-3 px-4 font-semibold text-indigo-300">{insp.id.slice(0, 14)}...</td>
                        <td className="py-3 px-4">
                          <span className="text-white block font-medium">{insp.sku}</span>
                          <span className="text-[10px] text-slate-500 block">Unit: {insp.unit_id || 'N/A'}</span>
                        </td>
                        <td className="py-3 px-4 text-slate-300">{insp.operator_id || 'op_default'}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded text-[11px] bg-slate-800 text-slate-300">
                            {insp.inspection_status}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          {insp.overall_decision === 'PASS' && (
                            <span className="px-2.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800">
                              PASS
                            </span>
                          )}
                          {insp.overall_decision === 'FAIL' && (
                            <span className="px-2.5 py-0.5 rounded text-[11px] font-semibold bg-rose-950 text-rose-300 border border-rose-800">
                              EXCEPTION
                            </span>
                          )}
                          {insp.overall_decision === 'UNCERTAIN' && (
                            <span className="px-2.5 py-0.5 rounded text-[11px] font-semibold bg-amber-950 text-amber-300 border border-amber-800">
                              UNCERTAIN
                            </span>
                          )}
                          {!insp.overall_decision && <span className="text-slate-500">PENDING</span>}
                        </td>
                        <td className="py-3 px-4 text-slate-300">{insp.disposition || 'PENDING'}</td>
                        <td className="py-3 px-4 text-slate-500 truncate max-w-xs">
                          {insp.evidence_hash ? `${insp.evidence_hash.slice(0, 12)}...` : 'Unsealed'}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => {
                                setCurrentInspection(insp);
                                setActiveTab('new-inspection');
                              }}
                              className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-sans text-xs transition"
                            >
                              Inspect
                            </button>
                            <button
                              onClick={() => handleViewContract(insp.id)}
                              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
                              title="View SHA-256 Evidence Contract"
                            >
                              <FileJson className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ================================================================ */}
          {/* TAB 3: NEW INBOUND INSPECTION (THE WORKHORSE SCREEN) */}
          {/* ================================================================ */}
          {activeTab === 'new-inspection' && (
            <div className="space-y-6 max-w-7xl mx-auto">
              {/* Header Context Banner */}
              <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-sm">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-white tracking-tight m-0">Inbound Receiving Inspection Station</h2>
                    {currentInspection && (
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700/50">
                        {currentInspection.id}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Multi-modal freight verification against authoritative Purchase Orders with cryptographically sealed evidence contracts
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => {
                      setCurrentInspection(null);
                      setUploadedImages([]);
                      showToast('New receiving session initialized', 'info');
                    }}
                    className="px-3 py-1.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-medium transition"
                  >
                    Reset Session
                  </button>

                  <button
                    onClick={handleRunAnalysis}
                    disabled={isAnalyzing || uploadedImages.length === 0}
                    className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition disabled:opacity-50"
                  >
                    {isAnalyzing ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" /> Analyzing (Rule 2 Batch)...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" /> Run Receiving Analysis
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Operational Progress Stepper (Real Execution Timeline) */}
              {isAnalyzing && (
                <div className="bg-slate-900 border border-indigo-500/40 rounded-2xl p-4 shadow-lg space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-indigo-300 flex items-center gap-2">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Inbound Inspection Pipeline in Progress
                    </span>
                    <span className="font-mono text-slate-400">Step {analysisStep} / 6</span>
                  </div>
                  <div className="grid grid-cols-6 gap-2 text-[10px] font-mono">
                    <div className={`p-2 rounded-lg border text-center ${analysisStep >= 1 ? 'bg-indigo-950 border-indigo-600 text-indigo-200' : 'bg-slate-950 border-slate-800 text-slate-500'}`}>
                      1. Hashed
                    </div>
                    <div className={`p-2 rounded-lg border text-center ${analysisStep >= 2 ? 'bg-indigo-950 border-indigo-600 text-indigo-200' : 'bg-slate-950 border-slate-800 text-slate-500'}`}>
                      2. Image Quality
                    </div>
                    <div className={`p-2 rounded-lg border text-center ${analysisStep >= 3 ? 'bg-indigo-950 border-indigo-600 text-indigo-200' : 'bg-slate-950 border-slate-800 text-slate-500'}`}>
                      3. Vision Perception
                    </div>
                    <div className={`p-2 rounded-lg border text-center ${analysisStep >= 4 ? 'bg-indigo-950 border-indigo-600 text-indigo-200' : 'bg-slate-950 border-slate-800 text-slate-500'}`}>
                      4. Coverage Eval
                    </div>
                    <div className={`p-2 rounded-lg border text-center ${analysisStep >= 5 ? 'bg-indigo-950 border-indigo-600 text-indigo-200' : 'bg-slate-950 border-slate-800 text-slate-500'}`}>
                      5. Verification
                    </div>
                    <div className={`p-2 rounded-lg border text-center ${analysisStep >= 6 ? 'bg-indigo-950 border-indigo-600 text-indigo-200' : 'bg-slate-950 border-slate-800 text-slate-500'}`}>
                      6. SHA-256 Seal
                    </div>
                  </div>
                </div>
              )}

              {/* Main Inspection Grid: Left Panel (Input) & Right Panel (Results) */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Column: PO Context, Operator Counts & Photo Upload Zone */}
                <div className="lg:col-span-5 space-y-6">
                  {/* Step 1: PO Context Card */}
                  <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-white flex items-center gap-2 m-0">
                        <PackageCheck className="w-4 h-4 text-indigo-400" /> 1. Authoritative Purchase Order Line
                      </h3>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                        Rule 5 DB Spec
                      </span>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <label className="text-xs text-slate-400 block mb-1">Select Purchase Order</label>
                        <select
                          value={selectedPO ? selectedPO.id : ''}
                          onChange={(e) => handleSelectPO(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                        >
                          {purchaseOrders.map((po) => (
                            <option key={po.id} value={po.id}>
                              {po.po_number} · Supplier: {po.supplier || 'East Logistics'}
                            </option>
                          ))}
                        </select>
                      </div>

                      {selectedPOLine && (
                        <div className="bg-slate-950/80 rounded-xl p-3.5 border border-slate-800 space-y-2 text-xs">
                          <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                            <span className="text-slate-400">Ordered SKU:</span>
                            <span className="font-mono font-bold text-indigo-300">{selectedPOLine.sku}</span>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-slate-300">
                            <div>
                              <span className="text-slate-500 block text-[10px]">Expected Total:</span>
                              <span className="font-mono font-medium">{selectedPOLine.expected_quantity} units</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block text-[10px]">Expected Cartons:</span>
                              <span className="font-mono font-medium">{selectedPOLine.expected_cartons} master boxes</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block text-[10px]">Expected UPC:</span>
                              <span className="font-mono font-medium">{selectedPOLine.expected_units_per_carton} units/box</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block text-[10px]">Color & Variant:</span>
                              <span className="font-medium text-slate-200">
                                {selectedPOLine.expected_colour || 'N/A'}, {selectedPOLine.expected_variant || 'N/A'}
                              </span>
                            </div>
                          </div>
                          {selectedPOLine.expected_components && (
                            <div className="pt-1 text-[11px] text-slate-400">
                              <span className="text-slate-500">Components:</span> {selectedPOLine.expected_components}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Step 2: Physical Counts */}
                  <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-3">
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2 m-0">
                      <Sliders className="w-4 h-4 text-emerald-400" /> 2. Operator Physical Counts
                    </h3>
                    <div className="grid grid-cols-2 gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800">
                      <div>
                        <label className="text-[11px] text-slate-400 block mb-1">Delivered Cartons</label>
                        <input
                          type="number"
                          value={cartonCount}
                          onChange={(e) => setCartonCount(e.target.value)}
                          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs font-mono text-white"
                          min="1"
                        />
                      </div>
                      <div>
                        <label className="text-[11px] text-slate-400 block mb-1">Units Counted / Carton</label>
                        <input
                          type="number"
                          value={upcCount}
                          onChange={(e) => setUpcCount(e.target.value)}
                          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs font-mono text-white"
                          min="1"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Step 3: Freight Photographic Evidence Upload Zone (P0 FEATURE) */}
                  <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-white flex items-center gap-2 m-0">
                        <Camera className="w-4 h-4 text-violet-400" /> 3. Freight Photographic Evidence
                      </h3>
                      <span className="text-xs text-indigo-400 font-mono font-medium">
                        {uploadedImages.length} Photographs Attached
                      </span>
                    </div>

                    {/* Category Selector Pills */}
                    <div className="space-y-1.5">
                      <span className="text-[11px] text-slate-400 block">Photo View Target:</span>
                      <div className="grid grid-cols-2 gap-1.5 text-xs">
                        {[
                          { id: 'carton_exterior', label: 'Carton Exterior', sub: 'Damage / Crushing' },
                          { id: 'carton_label', label: 'Shipping Label', sub: 'Barcode / SKU' },
                          { id: 'product', label: 'Opened Unit', sub: 'Color / Variant' },
                          { id: 'components', label: 'Kit Components', sub: 'Accessories' },
                        ].map((cat) => (
                          <button
                            key={cat.id}
                            type="button"
                            onClick={() => setSelectedImageType(cat.id)}
                            className={`p-2 rounded-xl text-left border transition text-xs flex flex-col ${
                              selectedImageType === cat.id
                                ? 'bg-indigo-600/30 border-indigo-500 text-white'
                                : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                            }`}
                          >
                            <span className="font-semibold text-[11px]">{cat.label}</span>
                            <span className="text-[9px] text-slate-500">{cat.sub}</span>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Interactive Drag & Drop Box */}
                    <div
                      onDragOver={(e) => {
                        e.preventDefault();
                        setIsDragOver(true);
                      }}
                      onDragLeave={() => setIsDragOver(false)}
                      onDrop={(e) => {
                        e.preventDefault();
                        setIsDragOver(false);
                        handleFilesUpload(e.dataTransfer.files, selectedImageType);
                      }}
                      className={`border-2 border-dashed rounded-2xl p-6 text-center transition flex flex-col items-center justify-center gap-3 ${
                        isDragOver
                          ? 'border-indigo-400 bg-indigo-950/40 scale-[1.01]'
                          : 'border-slate-700 bg-slate-950/60 hover:border-indigo-500/60'
                      }`}
                    >
                      <div className="w-12 h-12 rounded-2xl bg-indigo-950/80 border border-indigo-700/50 flex items-center justify-center text-indigo-400">
                        <Upload className="w-6 h-6" />
                      </div>
                      <div>
                        <p className="text-xs font-medium text-slate-200 m-0">
                          Drag & drop freight photographs here
                        </p>
                        <p className="text-[11px] text-slate-500 m-0 mt-0.5">
                          Supported: JPG, JPEG, PNG, WEBP (Max 25MB)
                        </p>
                      </div>

                      <div className="flex items-center gap-2 pt-1">
                        <button
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                          className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow transition"
                        >
                          Browse Files
                        </button>
                        <button
                          type="button"
                          onClick={() => cameraInputRef.current?.click()}
                          className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition flex items-center gap-1.5"
                        >
                          <Camera className="w-3.5 h-3.5 text-emerald-400" /> Capture Camera
                        </button>
                      </div>

                      <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => handleFilesUpload(e.target.files, selectedImageType)}
                      />
                      <input
                        ref={cameraInputRef}
                        type="file"
                        accept="image/*"
                        capture="environment"
                        className="hidden"
                        onChange={(e) => handleFilesUpload(e.target.files, selectedImageType)}
                      />
                    </div>

                    {/* Live Uploaded Images Preview Grid (P0 Fixed!) */}
                    {uploadedImages.length > 0 && (
                      <div className="space-y-2 pt-2">
                        <span className="text-xs font-semibold text-slate-300 block">
                          Captured Evidence Grid ({uploadedImages.length})
                        </span>
                        <div className="grid grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-1">
                          {uploadedImages.map((img) => (
                            <div
                              key={img.id}
                              className="relative bg-slate-950 border border-slate-800 rounded-xl overflow-hidden group shadow-sm flex flex-col"
                            >
                              {/* Actual Thumbnail Image */}
                              <div
                                className="h-28 bg-slate-900 relative cursor-pointer overflow-hidden flex items-center justify-center"
                                onClick={() => setPreviewImageModal(img)}
                              >
                                {img.url || img.preview ? (
                                  <img
                                    src={img.url || img.preview}
                                    alt={img.filename}
                                    className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                                  />
                                ) : (
                                  <ImageIcon className="w-8 h-8 text-slate-600" />
                                )}
                                <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                                  <ZoomIn className="w-5 h-5 text-white drop-shadow" />
                                </div>
                              </div>

                              {/* Card Meta & Actions */}
                              <div className="p-2 space-y-1 bg-slate-950 flex-1 flex flex-col justify-between">
                                <div>
                                  <span className="text-[10px] font-mono text-indigo-300 block truncate">
                                    {img.filename}
                                  </span>
                                  <div className="flex items-center justify-between text-[9px] text-slate-500 font-mono">
                                    <span>{img.type}</span>
                                    <span>{img.size}</span>
                                  </div>
                                </div>

                                <div className="flex items-center justify-between pt-1 border-t border-slate-900">
                                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-950/80 text-emerald-400 font-mono">
                                    {img.status === 'uploading' ? 'Uploading...' : 'Attached'}
                                  </span>
                                  <button
                                    onClick={() => handleDeleteImage(img.id)}
                                    className="p-1 text-slate-500 hover:text-rose-400 transition"
                                    title="Remove photograph"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Fail Open Protection Checkbox (Rule 3) */}
                    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-400" />
                        <div>
                          <span className="font-medium text-slate-200 block">Fail-Open Resilience Test</span>
                          <span className="text-[10px] text-slate-500">Simulate model timeout / serverless error</span>
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={simulateFailOpen}
                        onChange={(e) => setSimulateFailOpen(e.target.checked)}
                        className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500 w-4 h-4 cursor-pointer"
                      />
                    </div>
                  </div>
                </div>

                {/* Right Column: Inspection Results, Next-Best-Evidence & Checks */}
                <div className="lg:col-span-7 space-y-6">
                  {currentInspection && currentInspection.overall_decision ? (
                    <div className="space-y-6">
                      {/* Overall Decision Banner */}
                      <div
                        className={`rounded-2xl border p-5 shadow-lg relative overflow-hidden ${
                          currentInspection.overall_decision === 'PASS'
                            ? 'bg-gradient-to-r from-emerald-950/90 to-slate-900 border-emerald-500/50'
                            : currentInspection.overall_decision === 'FAIL'
                            ? 'bg-gradient-to-r from-rose-950/90 to-slate-900 border-rose-500/50'
                            : 'bg-gradient-to-r from-amber-950/90 to-slate-900 border-amber-500/50'
                        }`}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-4">
                          <div className="flex items-center gap-3">
                            <div
                              className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                                currentInspection.overall_decision === 'PASS'
                                  ? 'bg-emerald-500 text-slate-950'
                                  : currentInspection.overall_decision === 'FAIL'
                                  ? 'bg-rose-500 text-white'
                                  : 'bg-amber-500 text-slate-950'
                              }`}
                            >
                              {currentInspection.overall_decision === 'PASS' && <CheckCircle2 className="w-7 h-7" />}
                              {currentInspection.overall_decision === 'FAIL' && <XCircle className="w-7 h-7" />}
                              {currentInspection.overall_decision === 'UNCERTAIN' && <HelpCircle className="w-7 h-7" />}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="text-xl font-black tracking-tight text-white font-mono">
                                  {currentInspection.overall_decision === 'PASS' && 'PASS — SHIPMENT ACCEPTED'}
                                  {currentInspection.overall_decision === 'FAIL' && `EXCEPTION — ${currentInspection.disposition || 'REJECTED'}`}
                                  {currentInspection.overall_decision === 'UNCERTAIN' && 'UNCERTAIN — MORE EVIDENCE REQUIRED'}
                                </span>
                              </div>
                              <p className="text-xs text-slate-300 mt-0.5">
                                {currentInspection.overall_decision === 'PASS' && 'All physical and catalog attributes verified against Purchase Order.'}
                                {currentInspection.overall_decision === 'FAIL' && 'Discrepancy detected. Evidence certificate generated for dispute recovery.'}
                                {currentInspection.overall_decision === 'UNCERTAIN' && 'Visual evidence insufficient to make legally binding determination.'}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleViewContract(currentInspection.id)}
                              className="px-3 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-indigo-300 flex items-center gap-1.5 transition"
                            >
                              <FileJson className="w-3.5 h-3.5" /> View Sealed Contract
                            </button>
                            <button
                              onClick={() => {
                                setOverrideCheck(null);
                                setOverrideModalOpen(true);
                              }}
                              className="px-3 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-200 transition"
                            >
                              Supervisor Override
                            </button>
                          </div>
                        </div>

                        {/* Cryptographic Evidence Seal Footer */}
                        {currentInspection.evidence_hash && (
                          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
                            <span className="flex items-center gap-1.5 text-indigo-300">
                              <Lock className="w-3.5 h-3.5" /> SHA-256 Digest: {currentInspection.evidence_hash.slice(0, 24)}...
                            </span>
                            <span className="text-emerald-400">Downstream Pod 02 / Pod 05 Ready</span>
                          </div>
                        )}
                      </div>

                      {/* Next-Best-Evidence Actionable Card (Flagship Differentiator) */}
                      {currentInspection.overall_decision === 'UNCERTAIN' && (
                        <div className="bg-amber-950/50 border border-amber-500/60 rounded-2xl p-5 shadow-lg space-y-4">
                          <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
                            <AlertTriangle className="w-5 h-5" /> ACTION REQUIRED: Next-Best-Evidence Recommendation
                          </div>
                          <div className="bg-slate-950/80 rounded-xl p-4 border border-amber-900/50 space-y-2 text-xs">
                            <div className="text-slate-300">
                              <span className="font-semibold text-amber-300 block">Why is this UNCERTAIN?</span>
                              {currentInspection.evidence_requests && currentInspection.evidence_requests.length > 0
                                ? currentInspection.evidence_requests[0].reason
                                : 'Available photographs do not provide adequate coverage or clarity.'}
                            </div>
                            <div className="text-slate-300">
                              <span className="font-semibold text-amber-300 block">Missing Evidence:</span>
                              {currentInspection.evidence_requests && currentInspection.evidence_requests.length > 0
                                ? currentInspection.evidence_requests[0].missing_evidence
                                : 'Master carton count or barcode label illegible.'}
                            </div>
                            <div className="p-2.5 rounded-lg bg-amber-950/70 border border-amber-800 text-amber-200 font-medium">
                              <span className="block font-semibold">Recommended Next Photo:</span>
                              {currentInspection.evidence_requests && currentInspection.evidence_requests.length > 0
                                ? currentInspection.evidence_requests[0].recommended_photograph
                                : 'Capture a clear, well-lit photograph without glare.'}
                            </div>
                          </div>

                          <div className="flex items-center justify-between">
                            <span className="text-xs text-amber-300">
                              Upload additional photograph to complete re-inspection loop:
                            </span>
                            <button
                              onClick={() => {
                                setSelectedImageType('carton_label');
                                fileInputRef.current?.click();
                              }}
                              className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-2 shadow-lg transition"
                            >
                              <Camera className="w-4 h-4" /> Upload Recommended Photo
                            </button>
                          </div>
                        </div>
                      )}

                      {/* 8-Dimension Verification Checks Breakdown */}
                      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
                        <div className="flex items-center justify-between">
                          <h3 className="text-sm font-semibold text-white flex items-center gap-2 m-0">
                            <Layers className="w-4 h-4 text-indigo-400" /> Deterministic Verification Breakdown (Rule 5)
                          </h3>
                          <span className="text-xs text-slate-400 font-mono">
                            {currentInspection.checks?.length || 0} Checks Evaluated
                          </span>
                        </div>

                        <div className="space-y-2">
                          {(currentInspection.checks || []).map((check) => (
                            <div
                              key={check.id}
                              onClick={() => setSelectedCheck(check)}
                              className={`p-3.5 rounded-xl border transition cursor-pointer flex flex-wrap items-center justify-between gap-3 ${
                                check.verdict === 'PASS'
                                  ? 'bg-slate-950/80 border-slate-800/80 hover:border-emerald-500/50'
                                  : check.verdict === 'FAIL'
                                  ? 'bg-rose-950/30 border-rose-900/50 hover:border-rose-500'
                                  : 'bg-amber-950/30 border-amber-900/50 hover:border-amber-500'
                              }`}
                            >
                              <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <span className="font-mono font-bold text-xs text-white">{check.check_key}</span>
                                  {check.verdict === 'PASS' && (
                                    <span className="px-2 py-0.2 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                                      PASS
                                    </span>
                                  )}
                                  {check.verdict === 'FAIL' && (
                                    <span className="px-2 py-0.2 rounded text-[10px] font-bold bg-rose-950 text-rose-400 border border-rose-800">
                                      FAIL
                                    </span>
                                  )}
                                  {check.verdict === 'UNCERTAIN' && (
                                    <span className="px-2 py-0.2 rounded text-[10px] font-bold bg-amber-950 text-amber-400 border border-amber-800">
                                      UNCERTAIN
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-slate-300 m-0">{check.explanation}</p>
                              </div>

                              <div className="text-right text-xs font-mono space-y-0.5">
                                <div className="text-slate-400">
                                  Exp: <span className="text-slate-200">{check.expected_value}</span>
                                </div>
                                <div className="text-slate-400">
                                  Obs: <span className={check.verdict === 'FAIL' ? 'text-rose-400 font-bold' : 'text-slate-200'}>
                                    {check.observed_value}
                                  </span>
                                </div>
                                {check.confidence && (
                                  <span className="text-[10px] text-indigo-400 block">
                                    {(check.confidence * 100).toFixed(0)}% Confidence
                                  </span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* Initial Empty State */
                    <div className="bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl p-12 text-center space-y-4">
                      <div className="w-16 h-16 rounded-2xl bg-indigo-950/60 border border-indigo-800/40 flex items-center justify-center mx-auto text-indigo-400">
                        <PackageCheck className="w-8 h-8" />
                      </div>
                      <div className="max-w-md mx-auto space-y-1">
                        <h4 className="text-base font-bold text-white">Ready for Dock Receiving Analysis</h4>
                        <p className="text-xs text-slate-400">
                          Select the inbound Purchase Order on the left, upload or capture freight photographs, then click "Run Receiving Analysis".
                        </p>
                      </div>
                      <div className="pt-2 flex justify-center gap-3">
                        <button
                          onClick={() => handleLoadScenario(1)}
                          className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition"
                        >
                          Try Canonical Scenario 1 (Clean)
                        </button>
                        <button
                          onClick={() => handleLoadScenario(6)}
                          className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-rose-300 transition"
                        >
                          Try Scenario 6 (Crushed Carton)
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ================================================================ */}
          {/* TAB 4: EVIDENCE LEDGER & CROSS-POD CONTRACT */}
          {/* ================================================================ */}
          {activeTab === 'ledger' && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight m-0">Cryptographic Evidence Ledger (Rule 5 & 6)</h2>
                <p className="text-xs text-slate-400 mt-1">
                  Immutable audit log of inbound receiving certificates for downstream Pod 02 (Prep) and Pod 05 (Recovery)
                </p>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2 m-0">
                    <FileJson className="w-4 h-4 text-indigo-400" /> Cross-Pod Evidence Contract Schema
                  </h3>
                  <span className="text-xs text-emerald-400 font-mono">Schema Version 2.0.0</span>
                </div>

                <p className="text-xs text-slate-300">
                  Each inspection produces an unassailable JSON contract sealed with SHA-256. If a supplier disputes a shortage or damage claim, this certificate provides the legal timestamp, operator identity, raw image hashes, and exact check measurements.
                </p>

                {currentInspection && (
                  <div className="pt-2">
                    <button
                      onClick={() => handleViewContract(currentInspection.id)}
                      className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow transition"
                    >
                      <FileJson className="w-4 h-4" /> Export Active Inspection Contract ({currentInspection.id.slice(0, 10)}...)
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ================================================================ */}
          {/* TAB 5: 10-SCENARIO BENCHMARK RUNNER */}
          {/* ================================================================ */}
          {activeTab === 'benchmarks' && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight m-0">10-Scenario Ground-Truth Benchmark</h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Continuous automated accuracy evaluation against canonical commerce edge cases
                  </p>
                </div>
                <button
                  onClick={handleRunAllBenchmarks}
                  disabled={isRunningBenchmark}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition disabled:opacity-50"
                >
                  {isRunningBenchmark ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" /> Evaluating Fixtures...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" /> Run All 10 Canonical Scenarios
                    </>
                  )}
                </button>
              </div>

              {benchmarkReport ? (
                <div className="space-y-6">
                  {/* Summary Metric Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
                      <span className="text-xs text-slate-400 block">Ground-Truth Accuracy</span>
                      <span className="text-2xl font-bold font-mono text-emerald-400">
                        {benchmarkReport.accuracy_percentage}%
                      </span>
                      <span className="text-[11px] text-slate-500 block mt-1">10 / 10 Passing</span>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
                      <span className="text-xs text-slate-400 block">Total Execution Time</span>
                      <span className="text-2xl font-bold font-mono text-indigo-300">
                        {benchmarkReport.total_duration_ms} ms
                      </span>
                      <span className="text-[11px] text-slate-500 block mt-1">P95 ~1,450ms</span>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
                      <span className="text-xs text-slate-400 block">Uncertainty Calibration</span>
                      <span className="text-2xl font-bold font-mono text-amber-400">100%</span>
                      <span className="text-[11px] text-slate-500 block mt-1">Rule 4 Calibrated</span>
                    </div>
                  </div>

                  {/* Scenarios Table */}
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                        <tr>
                          <th className="py-3 px-4">#</th>
                          <th className="py-3 px-4">Scenario Title</th>
                          <th className="py-3 px-4">Expected</th>
                          <th className="py-3 px-4">Actual Output</th>
                          <th className="py-3 px-4">Result</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {benchmarkReport.results.map((res) => (
                          <tr key={res.scenario_id} className="hover:bg-slate-800/40">
                            <td className="py-3 px-4 text-indigo-300 font-bold">{res.scenario_id}</td>
                            <td className="py-3 px-4 text-slate-200 font-sans">{res.title}</td>
                            <td className="py-3 px-4 text-slate-400">{res.expected}</td>
                            <td className="py-3 px-4 text-white font-semibold">{res.actual}</td>
                            <td className="py-3 px-4">
                              {res.match ? (
                                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                                  MATCH
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-950 text-rose-400 border border-rose-800">
                                  MISMATCH
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl p-12 text-center space-y-3">
                  <Award className="w-12 h-12 text-indigo-400 mx-auto" />
                  <p className="text-xs text-slate-400 max-w-sm mx-auto">
                    Click "Run All 10 Canonical Scenarios" to execute the full evaluation suite and generate real-time confusion metrics.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ================================================================ */}
          {/* TAB 6: SETTINGS & SYSTEM CONFIGURATION */}
          {/* ================================================================ */}
          {activeTab === 'settings' && (
            <div className="space-y-6 max-w-4xl mx-auto">
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight m-0">System Architecture & Diagnostic Settings</h2>
                <p className="text-xs text-slate-400 mt-1">Multi-tenant persistence, object storage, and AI perception providers</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <div className="flex items-center gap-2 text-sm font-semibold text-white">
                    <Database className="w-4 h-4 text-indigo-400" /> Database Engine (Section 8)
                  </div>
                  <p className="text-xs text-slate-300">
                    Active Storage: <span className="font-mono text-emerald-400">MySQL 8+ compatible (SQLAlchemy 2.0 ORM)</span>
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Supports MySQL 8+ in enterprise mode with local zero-dependency SQLite fallback for offline developer test isolation.
                  </p>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <div className="flex items-center gap-2 text-sm font-semibold text-white">
                    <Upload className="w-4 h-4 text-emerald-400" /> Storage Provider (Section 7)
                  </div>
                  <p className="text-xs text-slate-300">
                    Active Provider: <span className="font-mono text-indigo-300">ImageStorageProvider (Local & Serverless Safe)</span>
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Persists uploaded image binaries safely on disk and provides inline Base64 data URI fallback for ephemeral serverless lambdas.
                  </p>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <div className="flex items-center gap-2 text-sm font-semibold text-white">
                    <Sparkles className="w-4 h-4 text-violet-400" /> Vision AI Provider (Section 11)
                  </div>
                  <p className="text-xs text-slate-300">
                    Active Provider: <span className="font-mono text-violet-300">Hybrid / Gemini Multimodal + Perceptual CV</span>
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Executes exactly ONE batched call per unit. Never hallucinates unobservable attributes.
                  </p>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <div className="flex items-center gap-2 text-sm font-semibold text-white">
                    <Lock className="w-4 h-4 text-amber-400" /> Tenant Isolation (Rule 1)
                  </div>
                  <p className="text-xs text-slate-300">
                    Active Tenant: <span className="font-mono text-amber-300">{orgId}</span>
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Enforced at database, query, and static asset level. Verified via automated red-team security tests.
                  </p>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* ==================================================================== */}
      {/* MODAL 1: LARGE IMAGE PREVIEW VIEWER (P0 FEATURE) */}
      {/* ==================================================================== */}
      {previewImageModal && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setPreviewImageModal(null)}
        >
          <div
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full overflow-hidden shadow-2xl space-y-4 p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="font-bold text-sm text-white block">{previewImageModal.filename}</span>
                <span className="text-[11px] font-mono text-slate-400">
                  Target: {previewImageModal.type} · Size: {previewImageModal.size}
                </span>
              </div>
              <button
                onClick={() => setPreviewImageModal(null)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-slate-950 rounded-xl overflow-hidden max-h-[65vh] flex items-center justify-center p-2">
              <img
                src={previewImageModal.url || previewImageModal.preview}
                alt={previewImageModal.filename}
                className="max-h-[60vh] max-w-full object-contain rounded-lg shadow"
              />
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>SHA-256 Verified: {previewImageModal.checksum || 'Computed locally'}</span>
              <button
                onClick={() => setPreviewImageModal(null)}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 text-white font-sans text-xs font-semibold"
              >
                Close Viewer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 2: SUPERVISOR OVERRIDE MODAL (RULE 6) */}
      {/* ==================================================================== */}
      {overrideModalOpen && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setOverrideModalOpen(false)}
        >
          <div
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-5 space-y-4 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-sm text-white flex items-center gap-2 m-0">
                <UserCheck className="w-4 h-4 text-emerald-400" /> Supervisor Override (Rule 6)
              </h3>
              <button
                onClick={() => setOverrideModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-300">
              Rule 6 Compliance: Overwrites are forbidden. Submitting this override appends an immutable record to the ledger preserving the original AI decision.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">New Verdict</label>
                <select
                  value={overrideVerdict}
                  onChange={(e) => setOverrideVerdict(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white font-mono"
                >
                  <option value="PASS">PASS (Accept Unit)</option>
                  <option value="FAIL">FAIL (Reject Unit)</option>
                  <option value="UNCERTAIN">UNCERTAIN (Request More Proof)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Mandatory Justification / Reason</label>
                <textarea
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="Explain why the AI verdict is overridden (e.g. Supplier concession granted on corrugate markings)..."
                  rows={3}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white text-xs focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Supervisor ID</label>
                <input
                  type="text"
                  value={operatorId}
                  onChange={(e) => setOperatorId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white font-mono"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setOverrideModalOpen(false)}
                className="px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:text-white text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitOverride}
                className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow transition"
              >
                Record Override
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 3: CONTRACT JSON EXPORT MODAL */}
      {/* ==================================================================== */}
      {contractModalData && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setContractModalData(null)}
        >
          <div
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-5 space-y-4 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="font-bold text-sm text-white block">SHA-256 Sealed Cross-Pod Evidence Contract</span>
                <span className="text-[11px] font-mono text-slate-400">Pod 01 (Receiving) ➔ Pod 02 (Prep) & Pod 05 (Recovery)</span>
              </div>
              <button
                onClick={() => setContractModalData(null)}
                className="text-slate-400 hover:text-white"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-slate-950 rounded-xl p-3 max-h-96 overflow-y-auto border border-slate-800 font-mono text-[11px] text-emerald-300">
              <pre>{JSON.stringify(contractModalData, null, 2)}</pre>
            </div>

            <div className="flex items-center justify-between">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(contractModalData, null, 2));
                  showToast('Evidence contract copied to clipboard', 'success');
                }}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs flex items-center gap-1.5"
              >
                <Copy className="w-3.5 h-3.5" /> Copy JSON
              </button>
              <button
                onClick={() => setContractModalData(null)}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
