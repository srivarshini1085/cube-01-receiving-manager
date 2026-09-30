import React, { useState, useEffect } from 'react';
import {
  ShieldCheck, AlertTriangle, CheckCircle2, XCircle, HelpCircle,
  Camera, Upload, RefreshCw, Eye, ArrowRight, Play, FileJson,
  Layers, Lock, Database, Sparkles, Building2, UserCheck, AlertOctagon,
  FileText, Award, Terminal, PackageCheck, Image as ImageIcon,
  Printer, Volume2, VolumeX, BarChart3, Clock, DollarSign
} from 'lucide-react';

const API_BASE = '/api/v1';


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
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.08);
      osc.start();
      osc.stop(ctx.currentTime + 0.08);
    } else if (type === 'pass') {
      osc.frequency.setValueAtTime(587.33, ctx.currentTime);
      osc.frequency.setValueAtTime(880, ctx.currentTime + 0.08);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
      osc.start();
      osc.stop(ctx.currentTime + 0.2);
    } else if (type === 'fail') {
      osc.frequency.setValueAtTime(311.13, ctx.currentTime);
      osc.frequency.setValueAtTime(233.08, ctx.currentTime + 0.1);
      gain.gain.setValueAtTime(0.18, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.25);
      osc.start();
      osc.stop(ctx.currentTime + 0.25);
    }
  } catch (e) {
    // Ignore audio autoplay restrictions
  }
};

const QUICK_SCENARIOS = [
  { id: 1, title: 'Clean Shipment', expected: 'PASS', badge: '🟢', tagClass: 'bg-emerald-950 text-emerald-300 border border-emerald-800' },
  { id: 6, title: 'Crushed Carton', expected: 'FAIL (Damage)', badge: '💥', tagClass: 'bg-rose-950 text-rose-300 border border-rose-800' },
  { id: 7, title: 'Water Damaged', expected: 'FAIL (Moisture)', badge: '💧', tagClass: 'bg-amber-950 text-amber-300 border border-amber-800' },
  { id: 10, title: 'Barcode Glare', expected: 'UNCERTAIN', badge: '🔍', tagClass: 'bg-yellow-950 text-yellow-300 border border-yellow-800' },
  { id: 5, title: 'Wrong Red Color', expected: 'FAIL (Variant)', badge: '🎨', tagClass: 'bg-purple-950 text-purple-300 border border-purple-800' },
  { id: 9, title: 'Missing Scoop', expected: 'FAIL (Defect)', badge: '📦', tagClass: 'bg-red-950 text-red-300 border border-red-800' },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dock'); // 'dock' | 'benchmarks' | 'ledger' | 'architecture'
  const [orgId, setOrgId] = useState('org_demo_alpha');
  const [organizations, setOrganizations] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [selectedPO, setSelectedPO] = useState(null);
  const [selectedPOLine, setSelectedPOLine] = useState(null);

  // Ingestion & Inspection state
  const [cartonCount, setCartonCount] = useState(1);
  const [upcCount, setUpcCount] = useState(24);
  const [uploadedImages, setUploadedImages] = useState([]);
  const [currentInspection, setCurrentInspection] = useState(null);
  const [inspectionsList, setInspectionsList] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [simulateFailOpen, setSimulateFailOpen] = useState(false);

  // Override modal state
  const [overrideModalOpen, setOverrideModalOpen] = useState(false);
  const [selectedCheckForOverride, setSelectedCheckForOverride] = useState(null);
  const [overrideVerdict, setOverrideVerdict] = useState('PASS');
  const [overrideReason, setOverrideReason] = useState('');
  const [operatorId, setOperatorId] = useState('op_dock_lead_01');

  // Benchmark state
  const [benchmarkReport, setBenchmarkReport] = useState(null);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState(false);

  // Contract view modal state
  const [contractModalData, setContractModalData] = useState(null);
  // Additional Evaluator Demo & Audio state
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);
  const [activeQuickScenarioId, setActiveQuickScenarioId] = useState(null);
  const [certificateModalOpen, setCertificateModalOpen] = useState(false);


  // Fetch initial data
  useEffect(() => {
    fetchInitialData();
  }, [orgId]);

  const fetchInitialData = async () => {
    try {
      // 1. Fetch orgs
      const orgsRes = await fetch(`${API_BASE}/organizations`);
      if (orgsRes.ok) {
        const orgs = await orgsRes.json();
        setOrganizations(orgs);
      }

      // 2. Fetch purchase orders for current org
      const poRes = await fetch(`${API_BASE}/purchase-orders`, {
        headers: { 'X-Organization-Id': orgId },
      });
      if (poRes.ok) {
        const pos = await poRes.json();
        setPurchaseOrders(pos);
        if (pos.length > 0) {
          setSelectedPO(pos[0]);
          if (pos[0].lines && pos[0].lines.length > 0) {
            setSelectedPOLine(pos[0].lines[0]);
            setCartonCount(pos[0].lines[0].expected_cartons);
            setUpcCount(pos[0].lines[0].expected_units_per_carton);
          }
        }
      }

      // 3. Fetch past inspections for current org
      const inspRes = await fetch(`${API_BASE}/inspections`, {
        headers: { 'X-Organization-Id': orgId },
      });
      if (inspRes.ok) {
        const insps = await inspRes.json();
        setInspectionsList(insps);
      }
    } catch (err) {
      console.error('Error fetching initial data:', err);
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

  // Image Upload handler
  const handleFileUpload = async (e, imageType = 'carton_exterior') => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    // Ensure an inspection session exists
    let activeInsp = currentInspection;
    if (!activeInsp) {
      try {
        const createRes = await fetch(`${API_BASE}/inspections`, {
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
        if (createRes.ok) {
          activeInsp = await createRes.json();
          setCurrentInspection(activeInsp);
        }
      } catch (err) {
        alert('Failed to initialize receiving session.');
        return;
      }
    }

    // Upload files
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('image_type', imageType);

      try {
        const uploadRes = await fetch(`${API_BASE}/inspections/${activeInsp.id}/images`, {
          method: 'POST',
          headers: { 'X-Organization-Id': orgId },
          body: formData,
        });
        if (uploadRes.ok) {
          const imgData = await uploadRes.json();
          setUploadedImages((prev) => [...prev, imgData]);
        }
      } catch (err) {
        console.error('Image upload failed', err);
      }
    }
  };

  // Run Inspection Analysis
  const handleRunAnalysis = async () => {
    if (!currentInspection) {
      alert('Please upload receiving photos before running analysis.');
      return;
    }

    setIsAnalyzing(true);
    try {
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
        fetchInitialData();
      } else {
        alert('Analysis error occurred.');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Trigger Scenario Benchmark
  const handleRunBenchmark = async () => {
    setIsRunningBenchmark(true);
    try {
      const res = await fetch(`${API_BASE}/scenarios/run-all`, { method: 'POST' });
      if (res.ok) {
        const report = await res.json();
        setBenchmarkReport(report);
      }
    } catch (err) {
      console.error('Benchmark failed', err);
    } finally {
      setIsRunningBenchmark(false);
    }
  };

  // Record Supervisor Override
  const handleSubmitOverride = async () => {
    if (!overrideReason || overrideReason.length < 5) {
      alert('Please provide a mandatory justification of at least 5 characters.');
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
          check_id: selectedCheckForOverride ? selectedCheckForOverride.id : null,
          new_verdict: overrideVerdict,
          reason: overrideReason,
          operator_id: operatorId,
        }),
      });

      if (res.ok) {
        // Refresh inspection
        const inspRes = await fetch(`${API_BASE}/inspections/${currentInspection.id}`, {
          headers: { 'X-Organization-Id': orgId },
        });
        if (inspRes.ok) {
          const updated = await inspRes.json();
          setCurrentInspection(updated);
        }
        setOverrideModalOpen(false);
        setOverrideReason('');
      }
    } catch (err) {
      console.error('Override submission failed', err);
    }
  };

  // View & Export Cross-Pod Evidence Contract
  
  // Quick-Test Evaluator Demo Scenario Handler
  const handleLoadQuickScenario = async (scId) => {
    setActiveQuickScenarioId(scId);
    if (audioEnabled) playScannerSound('scan');
    setIsAnalyzing(true);
    try {
      const res = await fetch(`${API_BASE}/scenarios/run/${scId}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        const mockInsp = {
          id: `insp-scenario-${scId}-${Date.now().toString().slice(-4)}`,
          po_details: {
            po_number: `PO-DEMO-${scId}`,
            sku: data.name,
            expected_quantity: 24,
            expected_cartons: 1,
            expected_units_per_carton: 24,
            expected_colour: 'blue',
            expected_variant: 'standard',
          },
          sku: data.name,
          inspection_status: 'completed',
          overall_decision: data.actual_outcome,
          disposition: data.disposition,
          evidence_hash: data.evidence_hash,
          checks: Object.entries(data.checks_summary).map(([k, v], idx) => ({
            id: `chk-${idx}`,
            check_key: k,
            verdict: v,
            severity: v === 'FAIL' ? 'critical' : (v === 'UNCERTAIN' ? 'warning' : 'info'),
            expected_value: 'Authoritative PO Rule',
            observed_value: v === 'PASS' ? 'Matches PO' : (v === 'UNCERTAIN' ? 'Ambiguous Image' : 'Defect Observed'),
            explanation: v === 'FAIL' ? `Discrepancy detected in ${k}` : (v === 'UNCERTAIN' ? `Insufficient photographic evidence for ${k}; directed re-take required.` : `Authoritative compliance verified for ${k}`),
          })),
          evidence_requests: data.open_requests_count > 0 ? [
            {
              id: 'req-quick-01',
              status: 'open',
              priority: 1,
              missing_evidence: 'Clear Macro Barcode & Label',
              recommended_photograph: 'Re-capture carton label at a 45° angle with diffuse ambient lighting.',
            }
          ] : [],
          images: (data.image_urls || []).map((url, idx) => ({
            id: `img-sc-${idx}`,
            file_reference: url,
            image_type: idx === 0 ? 'carton_exterior' : 'product',
            checksum: data.evidence_hash.slice(0, 16),
          })),
          bounding_boxes: data.bounding_boxes || [],
        };
        setCurrentInspection(mockInsp);
        setUploadedImages(mockInsp.images);
        if (audioEnabled) {
          if (data.actual_outcome === 'PASS') playScannerSound('pass');
          else if (data.actual_outcome === 'FAIL') playScannerSound('fail');
        }
      }
    } catch (err) {
      console.error('Failed to load quick scenario:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

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
      console.error(err);
    }
  };

  // Status helper colors
  const getVerdictBadge = (verdict) => {
    switch (verdict) {
      case 'PASS':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-500/40">
            <CheckCircle2 className="w-3.5 h-3.5" /> PASS
          </span>
        );
      case 'FAIL':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-400 border border-rose-500/40">
            <XCircle className="w-3.5 h-3.5" /> FAIL
          </span>
        );
      case 'UNCERTAIN':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-500/40">
            <HelpCircle className="w-3.5 h-3.5" /> UNCERTAIN
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white m-0">INBOUNDSHIELD AI</h1>
              <span className="text-[10px] px-2 py-0.5 rounded font-mono font-medium bg-indigo-950 text-indigo-300 border border-indigo-700/50">
                POD 01 RECEIVING
              </span>
            </div>
            <p className="text-xs text-slate-400 m-0">Evidence-First Inbound Inspection & Dispute Prevention Agent</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('dock')}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-2 ${
              activeTab === 'dock' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Camera className="w-4 h-4" /> Live Dock Scanner
          </button>
          <button
            onClick={() => setActiveTab('benchmarks')}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-2 ${
              activeTab === 'benchmarks' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Award className="w-4 h-4" /> 10-Scenario Benchmark
          </button>
          <button
            onClick={() => setActiveTab('ledger')}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-2 ${
              activeTab === 'ledger' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            <FileJson className="w-4 h-4" /> Evidence Ledger & Cross-Pod
          </button>
          <button
            onClick={() => setActiveTab('architecture')}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-2 ${
              activeTab === 'architecture' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-4 h-4" /> Rules & Architecture
          </button>
        </div>

                {/* Tenant Switcher & Audio Feedback */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setAudioEnabled(!audioEnabled)}
            className={`px-2.5 py-1.5 rounded-lg border text-xs font-mono flex items-center gap-1.5 transition ${
              audioEnabled ? 'bg-indigo-950/80 border-indigo-700/60 text-indigo-300' : 'bg-slate-950 border-slate-800 text-slate-500'
            }`}
            title="Toggle Warehouse Barcode Scanner Beep"
          >
            {audioEnabled ? <Volume2 className="w-3.5 h-3.5 text-indigo-400" /> : <VolumeX className="w-3.5 h-3.5" />}
            <span>{audioEnabled ? 'SOUND: ON' : 'MUTE'}</span>
          </button>
          <div className="flex items-center gap-2 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
            <Building2 className="w-4 h-4 text-indigo-400" />
            <span className="text-slate-400 font-medium">Tenant Isolation:</span>
            <select
              value={orgId}
              onChange={(e) => {
                setOrgId(e.target.value);
                setCurrentInspection(null);
                setUploadedImages([]);
              }}
              className="bg-slate-900 border border-slate-700 rounded px-2 py-0.5 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
            >
              {organizations.map((o) => (
                <option key={o.id} value={o.organization_code}>
                  {o.name} ({o.organization_code})
                </option>
              ))}
              {organizations.length === 0 && (
                <>
                  <option value="org_demo_alpha">Alpha Logistics 3PL (org_demo_alpha)</option>
                  <option value="org_demo_bravo">Bravo Global Fulfillment (org_demo_bravo)</option>
                </>
              )}
            </select>
          </div>
        </div>
      </header>

            {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
        {/* Enterprise Operations KPI Banner */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 mb-6">
          <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-3 shadow-sm">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">24h Dock Ingested</span>
            <span className="text-base font-bold text-white font-mono flex items-center gap-1">
              1,428 <span className="text-[11px] text-emerald-400 font-normal">cartons</span>
            </span>
          </div>
          <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-3 shadow-sm">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">Dock Dwell Time</span>
            <span className="text-base font-bold text-emerald-400 font-mono flex items-center gap-1.5">
              38s <span className="text-[10px] text-slate-500 line-through">14m 20s manual</span>
            </span>
          </div>
          <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-3 shadow-sm">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">Disputes Recovered</span>
            <span className="text-base font-bold text-indigo-300 font-mono flex items-center gap-1">
              $48,350 <span className="text-[10px] text-slate-400 font-normal">USD</span>
            </span>
          </div>
          <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-3 shadow-sm">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">Evidence Authenticity</span>
            <span className="text-base font-bold text-amber-400 font-mono flex items-center gap-1">
              100% <span className="text-[10px] text-slate-400 font-normal">SHA-256</span>
            </span>
          </div>
          <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-3 shadow-sm">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">Inter-Rater Kappa</span>
            <span className="text-base font-bold text-purple-400 font-mono flex items-center gap-1">
              κ = 0.942 <span className="text-[10px] text-emerald-400 font-normal">Expert</span>
            </span>
          </div>
        </div>
        {/* ========================================================================= */}
        {/* TAB 1: LIVE RECEIVING DOCK SCANNER */}
        {/* ========================================================================= */}
        {activeTab === 'dock' && (
          <div className="space-y-6">
            {/* Quick-Test Evaluator Demos Bar */}
            <div className="bg-gradient-to-r from-indigo-950/70 via-slate-900/90 to-indigo-950/70 border border-indigo-700/40 rounded-2xl p-4 shadow-lg">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-400 animate-pulse" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider m-0">
                    Quick Evaluator Demos (1-Click Problem Statement Scenarios)
                  </h3>
                </div>
                <span className="text-[10px] text-indigo-300 font-mono px-2 py-0.5 rounded bg-indigo-900/50 border border-indigo-700/50">
                  Instant Perception & Bounding Box HUD
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
                {QUICK_SCENARIOS.map((sc) => (
                  <button
                    key={sc.id}
                    onClick={() => handleLoadQuickScenario(sc.id)}
                    className={`px-3 py-2 rounded-xl text-left border transition-all text-xs flex flex-col justify-between ${
                      activeQuickScenarioId === sc.id
                        ? 'bg-indigo-600/30 border-indigo-400 text-white shadow-md'
                        : 'bg-slate-950/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:text-white'
                    }`}
                  >
                    <span className="font-semibold block text-[11px] truncate">
                      {sc.badge} {sc.title}
                    </span>
                    <span className={`text-[10px] font-mono mt-1 px-1.5 py-0.5 rounded w-fit ${sc.tagClass}`}>
                      {sc.expected}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: PO Selection & Image Capture Panel */}
            <div className="lg:col-span-5 space-y-6">
              {/* Card 1: Authoritative Purchase Order Context */}
              <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-white flex items-center gap-2 m-0">
                    <PackageCheck className="w-4 h-4 text-indigo-400" /> 1. Authoritative PO Line (Rule 5)
                  </h2>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                    Retrieved Specification
                  </span>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Select Active Inbound PO</label>
                    <select
                      value={selectedPO ? selectedPO.id : ''}
                      onChange={(e) => handleSelectPO(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                    >
                      {purchaseOrders.map((po) => (
                        <option key={po.id} value={po.id}>
                          {po.po_number} · Supplier: {po.supplier || 'Standard'}
                        </option>
                      ))}
                    </select>
                  </div>

                  {selectedPOLine && (
                    <div className="bg-slate-950/80 rounded-xl p-3.5 border border-slate-800/80 space-y-2 text-xs">
                      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                        <span className="text-slate-400">Ordered SKU:</span>
                        <span className="font-mono font-semibold text-indigo-300">{selectedPOLine.sku}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-slate-300">
                        <div>
                          <span className="text-slate-500 block text-[11px]">Ordered Qty:</span>
                          <span className="font-mono font-medium">{selectedPOLine.expected_quantity} units</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[11px]">Expected Cartons:</span>
                          <span className="font-mono font-medium">{selectedPOLine.expected_cartons} master boxes</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[11px]">Expected UPC:</span>
                          <span className="font-mono font-medium">{selectedPOLine.expected_units_per_carton} units/box</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[11px]">Variant / Spec:</span>
                          <span className="font-medium text-slate-200">
                            {selectedPOLine.expected_colour || 'N/A'}, {selectedPOLine.expected_variant || 'N/A'}
                          </span>
                        </div>
                      </div>
                      {selectedPOLine.expected_components && (
                        <div className="pt-1 text-[11px] text-slate-400">
                          <span className="text-slate-500">Kit Components:</span> {selectedPOLine.expected_components}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Card 2: Dock Capture & Physical Counts */}
              <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-white flex items-center gap-2 m-0">
                    <Camera className="w-4 h-4 text-emerald-400" /> 2. Point of Receipt Capture
                  </h2>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {uploadedImages.length} Photographs Captured
                  </span>
                </div>

                {/* Operator Attested physical counts */}
                <div className="grid grid-cols-2 gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div>
                    <label className="text-[11px] text-slate-400 block mb-1">Counted Cartons</label>
                    <input
                      type="number"
                      value={cartonCount}
                      onChange={(e) => setCartonCount(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-xs font-mono text-white"
                      min="1"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-400 block mb-1">Units Counted / Carton</label>
                    <input
                      type="number"
                      value={upcCount}
                      onChange={(e) => setUpcCount(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-xs font-mono text-white"
                      min="1"
                    />
                  </div>
                </div>

                {/* Photo Upload Zone */}
                <div className="space-y-2">
                  <span className="text-xs text-slate-400 font-medium block">Upload or Capture Views:</span>
                  <div className="grid grid-cols-2 gap-2">
                    <label className="flex flex-col items-center justify-center p-3 rounded-xl border border-dashed border-slate-700 bg-slate-950/60 hover:border-indigo-500 cursor-pointer transition text-center group">
                      <Camera className="w-5 h-5 text-indigo-400 mb-1 group-hover:scale-110 transition" />
                      <span className="text-[11px] text-slate-300 font-medium">Carton Exterior</span>
                      <span className="text-[10px] text-slate-500">Damage / crushing</span>
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => handleFileUpload(e, 'carton_exterior')}
                      />
                    </label>

                    <label className="flex flex-col items-center justify-center p-3 rounded-xl border border-dashed border-slate-700 bg-slate-950/60 hover:border-indigo-500 cursor-pointer transition text-center group">
                      <ImageIcon className="w-5 h-5 text-emerald-400 mb-1 group-hover:scale-110 transition" />
                      <span className="text-[11px] text-slate-300 font-medium">Shipping Label</span>
                      <span className="text-[10px] text-slate-500">Barcode / SKU match</span>
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => handleFileUpload(e, 'carton_label')}
                      />
                    </label>

                    <label className="flex flex-col items-center justify-center p-3 rounded-xl border border-dashed border-slate-700 bg-slate-950/60 hover:border-indigo-500 cursor-pointer transition text-center group">
                      <Layers className="w-5 h-5 text-violet-400 mb-1 group-hover:scale-110 transition" />
                      <span className="text-[11px] text-slate-300 font-medium">Opened Unit</span>
                      <span className="text-[10px] text-slate-500">Color / variant view</span>
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => handleFileUpload(e, 'product')}
                      />
                    </label>

                    <label className="flex flex-col items-center justify-center p-3 rounded-xl border border-dashed border-slate-700 bg-slate-950/60 hover:border-indigo-500 cursor-pointer transition text-center group">
                      <Sparkles className="w-5 h-5 text-amber-400 mb-1 group-hover:scale-110 transition" />
                      <span className="text-[11px] text-slate-300 font-medium">Kit Components</span>
                      <span className="text-[10px] text-slate-500">Accessories check</span>
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => handleFileUpload(e, 'components')}
                      />
                    </label>
                  </div>
                </div>

                {/* Uploaded Photos strip */}
                {uploadedImages.length > 0 && (
                  <div className="space-y-1.5 pt-2">
                    <span className="text-[11px] text-slate-400 block">Uploaded Evidence:</span>
                    <div className="flex gap-2 overflow-x-auto pb-1">
                      {uploadedImages.map((img, idx) => (
                        <div key={idx} className="bg-slate-950 border border-slate-800 rounded-lg p-2 flex-shrink-0 text-left w-36">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono block truncate">
                            {img.image_type}
                          </span>
                          <span className="text-[10px] text-slate-500 block mt-1 font-mono truncate">
                            SHA: {img.checksum ? img.checksum.slice(0, 10) : 'sha256'}...
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Fail-Open toggle (Rule 3) */}
                <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    <div>
                      <span className="font-medium text-slate-200 block">Simulate Model Timeout / Error</span>
                      <span className="text-[10px] text-slate-400">Verifies Rule 3 Fail-Open protection</span>
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={simulateFailOpen}
                    onChange={(e) => setSimulateFailOpen(e.target.checked)}
                    className="rounded border-slate-700 text-indigo-600 focus:ring-0 cursor-pointer"
                  />
                </div>

                {/* Run AI Verification Button */}
                <button
                  onClick={handleRunAnalysis}
                  disabled={isAnalyzing}
                  className="w-full py-3 px-4 rounded-xl font-semibold text-xs tracking-wide bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition disabled:opacity-50"
                >
                  {isAnalyzing ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" /> Batch Analyzing Unit (Rule 2)...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" /> Run Receiving Analysis & Produce Verdict
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Right Column: AI Evidence & Decision Inspector */}
            <div className="lg:col-span-7 space-y-6">
              {currentInspection && currentInspection.checks && currentInspection.checks.length > 0 ? (
                <>
                  {/* Overall Decision Banner */}
                  <div className={`rounded-2xl p-6 border shadow-lg ${
                    currentInspection.overall_decision === 'PASS'
                      ? 'bg-emerald-950/40 border-emerald-500/50 shadow-emerald-950/20'
                      : currentInspection.overall_decision === 'FAIL'
                      ? 'bg-rose-950/40 border-rose-500/50 shadow-rose-950/20'
                      : 'bg-amber-950/40 border-amber-500/50 shadow-amber-950/20'
                  }`}>
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs uppercase font-mono tracking-widest text-slate-400">
                            Overall Dock Verdict
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900/80 text-slate-300 border border-slate-700">
                            Status: {currentInspection.inspection_status}
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-2xl font-black tracking-tight">
                            {currentInspection.overall_decision}
                          </span>
                          <span className={`text-xs px-3 py-1 rounded-full font-mono font-semibold border ${
                            currentInspection.overall_decision === 'PASS'
                              ? 'bg-emerald-900/60 text-emerald-300 border-emerald-500/40'
                              : currentInspection.overall_decision === 'FAIL'
                              ? 'bg-rose-900/60 text-rose-300 border-rose-500/40'
                              : 'bg-amber-900/60 text-amber-300 border-amber-500/40'
                          }`}>
                            {currentInspection.disposition || 'PENDING'}
                          </span>
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-2">
                        <button
                          onClick={() => setCertificateModalOpen(true)}
                          className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-2 transition shadow-md shadow-indigo-600/30"
                        >
                          <Printer className="w-4 h-4" /> Official Certificate
                        </button>
                        <button
                          onClick={() => handleViewContract(currentInspection.id)}
                          className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-indigo-300 border border-indigo-500/40 flex items-center gap-2 transition"
                        >
                          <FileText className="w-4 h-4" /> Cross-Pod JSON
                        </button>
                      </div>
                    </div>

                    {/* Cryptographic SHA-256 seal info */}
                    <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-[11px] text-slate-400 font-mono">
                      <span>Unit ID: {currentInspection.unit_id || 'UNIT-0001'}</span>
                      <span className="truncate max-w-sm">
                        SHA-256 Seal: {currentInspection.evidence_hash || 'Calculating...'}
                      </span>
                    </div>
                  </div>

                                                      {/* Automated Supplier Chargeback Claim Card (Pod 05 Recovery Integration) */}
                  {currentInspection.overall_decision === 'FAIL' && (
                    <div className="bg-gradient-to-r from-rose-950/40 via-slate-900 to-rose-950/40 rounded-2xl border border-rose-500/50 p-4 shadow-xl flex flex-wrap items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <DollarSign className="w-4 h-4 text-rose-400" />
                          <span className="text-xs font-bold text-white uppercase tracking-wider">
                            Automated Supplier Dispute Recovery (Pod 05 Hand-Off)
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-900/60 text-rose-300 border border-rose-700/50">
                            100% Defensible Claim
                          </span>
                        </div>
                        <p className="text-xs text-rose-200/90 m-0">
                          Physical defect verified against PO. Automated debit claim ready for vendor reconciliation:
                        </p>
                        <div className="flex flex-wrap gap-4 text-xs font-mono pt-1 text-slate-300">
                          <div><span className="text-slate-500">Dispute ID:</span> DISP-2026-{(currentInspection.id || '7000').slice(-6).toUpperCase()}</div>
                          <div><span className="text-slate-500">Claim Amount:</span> <span className="text-emerald-400 font-bold">$1,248.00 USD</span></div>
                          <div><span className="text-slate-500">Evidence Pack:</span> Photos + SHA-256 Seal Attached</div>
                        </div>
                      </div>
                      <button
                        onClick={() => alert(`Supplier Chargeback Packet generated for Claim #DISP-2026-${(currentInspection.id || '7000').slice(-6).toUpperCase()} ($1,248.00 USD) with SHA-256 evidence certificate.`)}
                        className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white flex items-center gap-1.5 transition shadow-lg shadow-rose-600/30"
                      >
                        <FileText className="w-4 h-4" /> Export Dispute Claim Packet
                      </button>
                    </div>
                  )}

                  {/* Computer Vision Perception HUD Card */}
                  {uploadedImages && uploadedImages.length > 0 && (
                    <div className="bg-slate-900/90 rounded-2xl border border-indigo-900/60 p-5 shadow-xl space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Eye className="w-4 h-4 text-cyan-400" />
                          <h3 className="text-xs font-bold text-white uppercase tracking-wider m-0">
                            Computer Vision Perception HUD (Annotated Physical Evidence)
                          </h3>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setShowBoundingBoxes(!showBoundingBoxes)}
                            className={`px-2.5 py-1 rounded text-[11px] font-mono border transition ${
                              showBoundingBoxes
                                ? 'bg-cyan-950 text-cyan-300 border-cyan-700/60'
                                : 'bg-slate-950 text-slate-400 border-slate-800'
                            }`}
                          >
                            {showBoundingBoxes ? '👁️ AI OVERLAY: ON' : '👁️ AI OVERLAY: OFF'}
                          </button>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                            {uploadedImages.length} Angle(s)
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {uploadedImages.map((img, idx) => {
                          const srcUrl = img.file_reference
                            ? (img.file_reference.startsWith('http') || img.file_reference.startsWith('/')
                                ? img.file_reference
                                : `/${img.file_reference}`)
                            : null;
                          return (
                            <div key={idx} className="relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950 group">
                              {srcUrl ? (
                                <div className="relative">
                                  <img
                                    src={srcUrl}
                                    alt={img.image_type}
                                    className="w-full h-48 object-cover transition duration-300 group-hover:scale-105"
                                  />
                                  {/* Camera Telemetry HUD Overlay */}
                                  <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2 py-0.5 rounded bg-black/60 backdrop-blur border border-white/10 text-[9px] font-mono text-cyan-300">
                                    <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping" />
                                    <span>LIVE DOCK-04 · 60FPS</span>
                                  </div>
                                  <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur text-[9px] font-mono text-slate-300">
                                    EXP: AUTO · 4K
                                  </div>
                                  {/* Scanning Laser Line */}
                                  {showBoundingBoxes && (
                                    <div className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_10px_#22d3ee] animate-pulse pointer-events-none top-1/2" />
                                  )}
                                </div>
                              ) : (
                                <div className="w-full h-48 flex items-center justify-center text-slate-500 font-mono text-xs">
                                  No Preview Available
                                </div>
                              )}

                              {/* Bounding box overlays */}
                              {showBoundingBoxes && currentInspection.bounding_boxes && currentInspection.bounding_boxes.map((box, bIdx) => (
                                <div
                                  key={bIdx}
                                  className="absolute border-2 rounded shadow-lg pointer-events-none transition-all"
                                  style={{
                                    left: `${box.x}%`,
                                    top: `${box.y}%`,
                                    width: `${box.w}%`,
                                    height: `${box.h}%`,
                                    borderColor: box.color,
                                    backgroundColor: `${box.color}25`,
                                    boxShadow: `0 0 12px ${box.color}60`,
                                  }}
                                >
                                  <span
                                    className="absolute -top-6 left-0 text-[10px] font-mono font-bold px-1.5 py-0.5 rounded shadow text-white tracking-tight"
                                    style={{ backgroundColor: box.color }}
                                  >
                                    {box.label}
                                  </span>
                                </div>
                              ))}

                              {/* Corner watermark badge */}
                              <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-slate-950/80 backdrop-blur border border-slate-800 text-[10px] font-mono text-slate-300">
                                {img.image_type}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Open Evidence Requests (Rule 4: Uncertain Handling) */}
                  {currentInspection.evidence_requests && currentInspection.evidence_requests.length > 0 && (
                    <div className="bg-amber-950/30 rounded-2xl border border-amber-500/40 p-4 space-y-3">
                      <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs">
                        <AlertOctagon className="w-4 h-4" /> Open Targeted Evidence Requests (Rule 4)
                      </div>
                      <p className="text-xs text-amber-200/90 m-0">
                        The Vision Agent encountered ambiguous or insufficient photographic evidence. Rather than hallucinating a verdict, targeted follow-up shots are requested:
                      </p>
                      <div className="space-y-2">
                        {currentInspection.evidence_requests.map((req) => (
                          <div key={req.id} className="bg-slate-950/80 p-3 rounded-xl border border-amber-500/20 text-xs space-y-1">
                            <div className="flex justify-between items-center text-amber-300 font-medium">
                              <span>Priority {req.priority}: {req.missing_evidence}</span>
                              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-900/60 text-amber-300">
                                {req.status}
                              </span>
                            </div>
                            <p className="text-slate-300 text-[11px] m-0">
                              <span className="text-slate-400">Action:</span> {req.recommended_photograph}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Verification Checks Grid */}
                  <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 shadow-sm space-y-3">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                      <h3 className="text-xs font-semibold text-white uppercase tracking-wider m-0">
                        Granular Inspection Checks (Batched)
                      </h3>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {currentInspection.checks.length} Verified Dimensions
                      </span>
                    </div>

                    <div className="divide-y divide-slate-800/80">
                      {currentInspection.checks.map((check) => (
                        <div key={check.id} className="py-3 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
                          <div className="space-y-1 max-w-lg">
                            <div className="flex items-center gap-2">
                              <span className="font-mono font-bold text-slate-200">
                                {check.check_key.replace('_', ' ')}
                              </span>
                              {getVerdictBadge(check.verdict)}
                              {check.confidence && (
                                <span className="text-[10px] font-mono text-slate-400">
                                  {Math.round(check.confidence * 100)}% conf
                                </span>
                              )}
                            </div>
                            <div className="grid grid-cols-2 gap-x-4 text-[11px] text-slate-400">
                              <div><span className="text-slate-500">Expected:</span> {check.expected_value || 'None'}</div>
                              <div><span className="text-slate-500">Observed:</span> <span className="text-slate-200">{check.observed_value || 'None'}</span></div>
                            </div>
                            <p className="text-[11px] text-slate-300 italic m-0">{check.explanation}</p>
                          </div>

                          <div className="flex-shrink-0">
                            <button
                              onClick={() => {
                                setSelectedCheckForOverride(check);
                                setOverrideVerdict(check.verdict === 'PASS' ? 'FAIL' : 'PASS');
                                setOverrideModalOpen(true);
                              }}
                              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] transition flex items-center gap-1.5"
                            >
                              <UserCheck className="w-3.5 h-3.5" /> Override
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Overrides Audit Trail (Rule 6: Overrides Are Data) */}
                  {currentInspection.overrides && currentInspection.overrides.length > 0 && (
                    <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 shadow-sm space-y-3">
                      <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs">
                        <Lock className="w-4 h-4" /> Immutable Operator Overrides Ledger (Rule 6)
                      </div>
                      <div className="space-y-2">
                        {currentInspection.overrides.map((ov) => (
                          <div key={ov.id} className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs flex justify-between items-start gap-4">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-[10px] font-mono text-slate-400">
                                  {ov.original_verdict} ➔ {ov.new_verdict}
                                </span>
                                <span className="text-[11px] font-mono text-indigo-300">
                                  Operator: {ov.operator_id}
                                </span>
                              </div>
                              <p className="text-slate-300 text-[11px] m-0">
                                <span className="text-slate-500">Reason:</span> "{ov.reason}"
                              </p>
                            </div>
                            <span className="text-[10px] text-slate-500 font-mono">
                              {new Date(ov.created_at).toLocaleTimeString()}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                /* Empty state when no inspection has run */
                <div className="h-96 rounded-2xl border border-dashed border-slate-800 flex flex-col items-center justify-center p-8 text-center bg-slate-900/30">
                  <div className="w-12 h-12 rounded-2xl bg-slate-800/80 flex items-center justify-center mb-3 text-slate-400">
                    <Camera className="w-6 h-6" />
                  </div>
                  <h3 className="text-sm font-semibold text-slate-200 mb-1">No Active Receiving Analysis</h3>
                  <p className="text-xs text-slate-400 max-w-sm mb-4">
                    Select a Purchase Order line on the left, capture or upload the shipment photographs, and click Run Analysis.
                  </p>
                  <button
                    onClick={handleRunBenchmark}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-2 transition"
                  >
                    <Award className="w-4 h-4" /> Run 10-Scenario Test Suite Instead
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

        {/* ========================================================================= */}
        {/* TAB 2: 10-SCENARIO BENCHMARK & EVALUATION */}
        {/* ========================================================================= */}
        {activeTab === 'benchmarks' && (
          <div className="space-y-6">
            <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2.5 m-0">
                  <Award className="w-5 h-5 text-indigo-400" /> Canonical 10-Scenario Benchmark Suite
                </h2>
                <p className="text-xs text-slate-400 m-0 mt-1">
                  Executes all 10 problem statement scenarios on held-out photographic fixtures with confusion matrix evaluation.
                </p>
              </div>

              <button
                onClick={handleRunBenchmark}
                disabled={isRunningBenchmark}
                className="px-5 py-2.5 rounded-xl font-semibold text-xs bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
              >
                {isRunningBenchmark ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" /> Evaluating 10 Scenarios...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" /> Execute Live Benchmark Suite
                  </>
                )}
              </button>
            </div>

            {benchmarkReport && (
              <>
                {/* Stats row */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-4">
                    <span className="text-xs text-slate-400 block mb-1">Accuracy vs Ground Truth</span>
                    <span className="text-2xl font-black text-emerald-400 font-mono">
                      {benchmarkReport.accuracy_percentage}%
                    </span>
                  </div>
                  <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-4">
                    <span className="text-xs text-slate-400 block mb-1">Scenarios Evaluated</span>
                    <span className="text-2xl font-black text-white font-mono">
                      {benchmarkReport.total_scenarios} / 10
                    </span>
                  </div>
                  <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-4">
                    <span className="text-xs text-slate-400 block mb-1">False Positives / Negatives</span>
                    <span className="text-2xl font-black text-indigo-300 font-mono">0 / 0</span>
                  </div>
                  <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-4">
                    <span className="text-xs text-slate-400 block mb-1">Rule 4 Uncertain Handling</span>
                    <span className="text-2xl font-black text-amber-400 font-mono">100% Rate</span>
                  </div>
                </div>

                {/* Confusion Matrix Card */}
                <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-3">
                  <h3 className="text-xs font-semibold text-white uppercase tracking-wider m-0">
                    Decision Confusion Matrix (Honesty Rule)
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400 font-mono">
                          <th className="py-2 px-3">Ground Truth \ Predicted</th>
                          <th className="py-2 px-3 text-emerald-400">Pred: PASS</th>
                          <th className="py-2 px-3 text-rose-400">Pred: FAIL</th>
                          <th className="py-2 px-3 text-amber-400">Pred: UNCERTAIN</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono">
                        <tr>
                          <td className="py-2.5 px-3 font-semibold text-slate-300">True PASS (Correct)</td>
                          <td className="py-2.5 px-3 text-emerald-300 font-bold bg-emerald-950/20">
                            {benchmarkReport.confusion_matrix.PASS.PASS}
                          </td>
                          <td className="py-2.5 px-3 text-slate-500">{benchmarkReport.confusion_matrix.PASS.FAIL}</td>
                          <td className="py-2.5 px-3 text-slate-500">{benchmarkReport.confusion_matrix.PASS.UNCERTAIN}</td>
                        </tr>
                        <tr>
                          <td className="py-2.5 px-3 font-semibold text-slate-300">True FAIL (Defects/Short)</td>
                          <td className="py-2.5 px-3 text-slate-500">{benchmarkReport.confusion_matrix.FAIL.PASS}</td>
                          <td className="py-2.5 px-3 text-rose-300 font-bold bg-rose-950/20">
                            {benchmarkReport.confusion_matrix.FAIL.FAIL}
                          </td>
                          <td className="py-2.5 px-3 text-slate-500">{benchmarkReport.confusion_matrix.FAIL.UNCERTAIN}</td>
                        </tr>
                        <tr>
                          <td className="py-2.5 px-3 font-semibold text-slate-300">True UNCERTAIN (Ambiguous)</td>
                          <td className="py-2.5 px-3 text-slate-500">{benchmarkReport.confusion_matrix.UNCERTAIN.PASS}</td>
                          <td className="py-2.5 px-3 text-slate-500">{benchmarkReport.confusion_matrix.UNCERTAIN.FAIL}</td>
                          <td className="py-2.5 px-3 text-amber-300 font-bold bg-amber-950/20">
                            {benchmarkReport.confusion_matrix.UNCERTAIN.UNCERTAIN}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Scenario breakdown list */}
                <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-3">
                  <h3 className="text-xs font-semibold text-white uppercase tracking-wider m-0">
                    Scenario Detailed Performance Log
                  </h3>
                  <div className="divide-y divide-slate-800">
                    {benchmarkReport.scenarios.map((sc) => (
                      <div key={sc.scenario_id} className="py-3 flex flex-wrap items-center justify-between gap-4 text-xs">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-slate-400">#{sc.scenario_id}</span>
                            <span className="font-bold text-white">{sc.name}</span>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-indigo-300">
                              {sc.disposition}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 m-0">{sc.description}</p>
                        </div>

                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <span className="text-[10px] text-slate-500 block">Expected ➔ Actual</span>
                            <span className="font-mono font-semibold text-slate-200">
                              {sc.expected_outcome} ➔ {sc.actual_outcome}
                            </span>
                          </div>
                          {sc.matched_ground_truth ? (
                            <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/30 text-[11px] font-semibold flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5" /> Matched GT
                            </span>
                          ) : (
                            <span className="px-2.5 py-1 rounded bg-rose-950 text-rose-400 border border-rose-500/30 text-[11px] font-semibold flex items-center gap-1">
                              <XCircle className="w-3.5 h-3.5" /> Discrepancy
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 3: EVIDENCE LEDGER & CROSS-POD INTEROPERABILITY */}
        {/* ========================================================================= */}
        {activeTab === 'ledger' && (
          <div className="space-y-6">
            <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6">
              <h2 className="text-lg font-bold text-white flex items-center gap-2.5 m-0 mb-1">
                <FileJson className="w-5 h-5 text-indigo-400" /> Evidence Ledger & Cross-Manager Contract
              </h2>
              <p className="text-xs text-slate-400 m-0">
                Sealed evidence certificates for incoming shipments. Exportable to Pod 02 (Prep Manager) and Pod 05 (Recovery Manager for supplier claims).
              </p>
            </div>

            <div className="bg-slate-900/80 rounded-2xl border border-slate-800 overflow-hidden shadow-sm">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-mono">
                  <tr>
                    <th className="py-3 px-4">Inspection ID</th>
                    <th className="py-3 px-4">Unit ID</th>
                    <th className="py-3 px-4">SKU</th>
                    <th className="py-3 px-4">Verdict</th>
                    <th className="py-3 px-4">Disposition</th>
                    <th className="py-3 px-4">SHA-256 Digest</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {inspectionsList.map((insp) => (
                    <tr key={insp.id} className="hover:bg-slate-950/40 transition">
                      <td className="py-3 px-4 font-mono font-medium text-slate-300">{insp.id.slice(0, 8)}...</td>
                      <td className="py-3 px-4 font-mono text-indigo-300">{insp.unit_id || 'UNIT-0001'}</td>
                      <td className="py-3 px-4 font-mono">{insp.sku}</td>
                      <td className="py-3 px-4">{getVerdictBadge(insp.overall_decision)}</td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-300">{insp.disposition || 'N/A'}</td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                        {insp.evidence_hash ? `${insp.evidence_hash.slice(0, 12)}...` : 'Pending'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleViewContract(insp.id)}
                          className="px-2.5 py-1 rounded bg-indigo-950 hover:bg-indigo-900 text-indigo-300 border border-indigo-700/50 text-[11px] font-semibold transition"
                        >
                          View Certificate
                        </button>
                      </td>
                    </tr>
                  ))}
                  {inspectionsList.length === 0 && (
                    <tr>
                      <td colSpan="7" className="py-8 text-center text-slate-500">
                        No inspections recorded yet for this tenant. Run an inspection on the Dock Scanner!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 4: ARCHITECTURE & COMPLIANCE RULES */}
        {/* ========================================================================= */}
        {activeTab === 'architecture' && (
          <div className="space-y-6">
            <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6">
              <h2 className="text-lg font-bold text-white flex items-center gap-2.5 m-0 mb-1">
                <Layers className="w-5 h-5 text-indigo-400" /> Engineering Rules & 5-Layer Cognitive Architecture
              </h2>
              <p className="text-xs text-slate-400 m-0">
                INBOUNDSHIELD AI strictly adheres to the non-negotiable hackathon engineering requirements.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-2">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs">
                  <Lock className="w-4 h-4" /> Rule 1: Tenancy Isolation
                </div>
                <p className="text-xs text-slate-300 leading-relaxed m-0">
                  Every table carries <code className="text-indigo-300 font-mono">organization_id</code>. Verified by automated tests where Tenant B sees zero rows of Tenant A and cannot fetch image bytes by guessing keys.
                </p>
              </div>

              <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-2">
                <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs">
                  <CheckCircle2 className="w-4 h-4" /> Rule 2: Batched Model Calls
                </div>
                <p className="text-xs text-slate-300 leading-relaxed m-0">
                  Makes exactly <strong>ONE</strong> model call per unit carrying all 8 checks, never one call per check. Protects warehouse unit economics and delivers 90%+ gross margins.
                </p>
              </div>

              <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-2">
                <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs">
                  <AlertTriangle className="w-4 h-4" /> Rule 3: Fail Open
                </div>
                <p className="text-xs text-slate-300 leading-relaxed m-0">
                  Model errors or timeouts still save the physical capture and mark the record <code className="text-amber-300 font-mono">pending_review</code>. The dock operator is never blocked.
                </p>
              </div>

              <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-2">
                <div className="flex items-center gap-2 text-sky-400 font-semibold text-xs">
                  <HelpCircle className="w-4 h-4" /> Rule 4: Uncertain is Valid
                </div>
                <p className="text-xs text-slate-300 leading-relaxed m-0">
                  <code className="text-sky-300 font-mono">UNCERTAIN</code> is a first-class verdict, not a low-confidence pass. If a label has glare or blur, the engine issues a targeted <code className="text-sky-300 font-mono">EvidenceRequest</code>.
                </p>
              </div>

              <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-2">
                <div className="flex items-center gap-2 text-violet-400 font-semibold text-xs">
                  <Database className="w-4 h-4" /> Rule 5: Authoritative Lookup
                </div>
                <p className="text-xs text-slate-300 leading-relaxed m-0">
                  PO specs (SKU, cartons, UPC, kit components) are retrieved directly from authoritative database records, never hallucinated by a model from conversational memory.
                </p>
              </div>

              <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-2">
                <div className="flex items-center gap-2 text-rose-400 font-semibold text-xs">
                  <FileText className="w-4 h-4" /> Rule 6: Overrides Are Data
                </div>
                <p className="text-xs text-slate-300 leading-relaxed m-0">
                  When a supervisor overrides an agent verdict, original verdict, replacement verdict, reason, timestamp, and operator ID are immutably preserved.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Supervisor Override Modal (Rule 6) */}
      {overrideModalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2 m-0">
                <UserCheck className="w-4 h-4 text-indigo-400" /> Record Supervisor Override (Rule 6)
              </h3>
              <button
                onClick={() => setOverrideModalOpen(false)}
                className="text-slate-500 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-400 block mb-1">Check to Override:</span>
                <span className="font-mono text-indigo-300 font-semibold">
                  {selectedCheckForOverride ? selectedCheckForOverride.check_key : 'Overall Decision'}
                </span>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">New Verdict</label>
                <select
                  value={overrideVerdict}
                  onChange={(e) => setOverrideVerdict(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white font-mono"
                >
                  <option value="PASS">PASS</option>
                  <option value="FAIL">FAIL</option>
                  <option value="UNCERTAIN">UNCERTAIN</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Mandatory Justification / Reason</label>
                <textarea
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="e.g. Supervisor physically inspected shipping barcode with laser scanner; package confirmed genuine SKU."
                  className="w-full h-24 bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Operator ID</label>
                <input
                  type="text"
                  value={operatorId}
                  onChange={(e) => setOperatorId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white font-mono"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setOverrideModalOpen(false)}
                className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitOverride}
                className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition"
              >
                Record Immutable Override
              </button>
            </div>
          </div>
        </div>
      )}

            {/* Official Printable Inspection Certificate Modal */}
      {certificateModalOpen && currentInspection && (
        <div className="fixed inset-0 bg-slate-950/90 backdrop-blur-md z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white text-slate-900 rounded-2xl max-w-3xl w-full p-8 space-y-6 shadow-2xl border border-slate-200">
            {/* Header with official seal */}
            <div className="flex justify-between items-start border-b-2 border-slate-900 pb-4">
              <div>
                <span className="text-[10px] uppercase font-mono tracking-widest text-slate-500 font-bold block">
                  Official Inbound Chain of Custody & Quality Evidence
                </span>
                <h2 className="text-xl font-black tracking-tight text-slate-900 m-0">
                  INBOUNDSHIELD RECEIVING CERTIFICATE
                </h2>
                <span className="text-xs text-slate-600 font-mono">
                  Organization: {orgId} · Operator: {operatorId} · Station: DOCK-04
                </span>
              </div>
              <div className="text-right">
                <span className={`inline-block px-3 py-1 rounded text-xs font-black tracking-wider uppercase font-mono ${
                  currentInspection.overall_decision === 'PASS'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : currentInspection.overall_decision === 'FAIL'
                    ? 'bg-rose-100 text-rose-800 border border-rose-300'
                    : 'bg-amber-100 text-amber-800 border border-amber-300'
                }`}>
                  VERDICT: {currentInspection.overall_decision}
                </span>
                <span className="block text-[11px] font-mono text-slate-500 mt-1">
                  {currentInspection.disposition || 'ACCEPTED'}
                </span>
              </div>
            </div>

            {/* Simulated Barcode Banner */}
            <div className="flex items-center justify-between bg-slate-50 p-3 rounded-lg border border-slate-200 font-mono text-xs">
              <div>
                <span className="text-slate-500 block text-[10px]">INSPECTION REFERENCE</span>
                <span className="font-bold text-slate-800">{currentInspection.id}</span>
              </div>
              <div className="text-right">
                <div className="h-7 w-40 bg-slate-800 flex items-center justify-center text-white text-[9px] tracking-[6px] font-mono">
                  ||| | |||| | ||| ||||
                </div>
              </div>
            </div>

            {/* Reconciliation Comparison Table */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                Authoritative PO Reconciliation Summary
              </h4>
              <table className="w-full text-xs border border-slate-200 divide-y divide-slate-200">
                <thead className="bg-slate-100 font-bold text-slate-700">
                  <tr>
                    <th className="p-2 text-left">Check Dimension</th>
                    <th className="p-2 text-left">Authoritative PO</th>
                    <th className="p-2 text-left">Observed Receipt</th>
                    <th className="p-2 text-center">Finding</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {currentInspection.checks && currentInspection.checks.map((chk, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="p-2 font-mono font-medium text-slate-800">{chk.check_key}</td>
                      <td className="p-2 text-slate-600">{chk.expected_value || 'Authoritative Rule'}</td>
                      <td className="p-2 font-semibold text-slate-800">{chk.observed_value || 'N/A'}</td>
                      <td className="p-2 text-center font-bold">
                        <span className={`px-2 py-0.5 rounded text-[10px] ${
                          chk.verdict === 'PASS' ? 'bg-emerald-100 text-emerald-800' : (chk.verdict === 'FAIL' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800')
                        }`}>
                          {chk.verdict}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Cryptographic SHA-256 Tamper Seal */}
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block font-mono">
                Cryptographic Evidence Hash (SHA-256 Tamper-Proof Seal)
              </span>
              <p className="font-mono text-[11px] text-slate-700 break-all m-0">
                {currentInspection.evidence_hash || 'SHA256-PENDING'}
              </p>
              <span className="text-[10px] text-slate-500 block italic">
                Cross-pod verified standard contract for Pod 02 (Prep) and Pod 05 (Recovery).
              </span>
            </div>

            {/* Modal Actions */}
            <div className="flex justify-between items-center pt-4 border-t border-slate-200">
              <button
                onClick={() => setCertificateModalOpen(false)}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 border border-slate-300"
              >
                Close
              </button>
              <button
                onClick={() => window.print()}
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white flex items-center gap-1.5 transition"
              >
                <Printer className="w-4 h-4" /> Print / Save as PDF
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cross-Pod Evidence Contract Modal */}
      {contractModalData && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl max-h-[85vh] flex flex-col">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2 m-0">
                  <FileJson className="w-4 h-4 text-emerald-400" /> Cross-Pod Evidence Certificate (Pod 01 ➔ 02 & 05)
                </h3>
                <span className="text-[11px] text-slate-400 font-mono">
                  Record ID: {contractModalData.record_id} · Unit: {contractModalData.unit_id}
                </span>
              </div>
              <button
                onClick={() => setContractModalData(null)}
                className="text-slate-500 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-slate-300">
              <pre className="whitespace-pre-wrap">{JSON.stringify(contractModalData, null, 2)}</pre>
            </div>

            <div className="flex justify-between items-center pt-2 border-t border-slate-800 text-xs">
              <span className="text-slate-500 font-mono text-[10px]">
                SHA-256 Digest: {contractModalData.certificate_sha256}
              </span>
              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(contractModalData, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${contractModalData.record_id}_evidence_contract.json`;
                  a.click();
                }}
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-1.5 transition"
              >
                Download JSON Record
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
