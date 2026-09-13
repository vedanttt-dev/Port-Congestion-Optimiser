# Light-theme token swap for all dashboard pages
$root = 'd:\ship-managment\frontend\src\pages'
$files = @('OverviewPage.tsx','DataPage.tsx','PredictPage.tsx','OptimizePage.tsx','PlanPage.tsx')

$replacements = @(
  ('bg-gradient-to-r from-\[#0e1a33\] via-\[#101f3d\] to-\[#0e1a33\]', 'bg-gradient-to-r from-slate-50 via-white to-slate-50')
  ('bg-gradient-to-r from-\[#08251f\] via-\[#0a2b26\] to-\[#0e1a33\]', 'bg-gradient-to-r from-slate-50 via-white to-slate-50')
  ('bg-gradient-to-r from-\[#2a1a05\] via-\[#241a08\] to-\[#0e1a33\]', 'bg-gradient-to-r from-slate-50 via-white to-slate-50')
  ('bg-gradient-to-r from-\[#181233\] via-\[#171430\] to-\[#0e1a33\]', 'bg-gradient-to-r from-slate-50 via-white to-slate-50')
  ('bg-cyan-500/10','bg-cyan-200/40')
  ('bg-violet-500/10','bg-violet-200/40')
  ('bg-emerald-500/10','bg-emerald-200/40')
  ('bg-rose-500/10','bg-rose-200/40')
  ('bg-sky-500/10','bg-sky-200/40')
  ('bg-pink-500/10','bg-pink-200/40')
  ('bg-teal-500/10','bg-teal-200/40')
  ('bg-amber-500/10','bg-amber-200/40')
  ('bg-fuchsia-500/10','bg-fuchsia-200/40')
  ('text-white','text-port-text')
  ('placeholder-slate-500','placeholder-port-muted')
  ('bg-slate-900/60','bg-slate-200/60')
  ('bg-slate-900/85','bg-white/90')
  ('bg-slate-900/80','bg-slate-300/95')
  ('bg-slate-800/60','bg-slate-200/60')
  ('bg-slate-800/70','bg-slate-300/70')
  ('bg-slate-800','bg-slate-300')
  ('bg-slate-900','bg-slate-200')
  ('bg-slate-700/60','bg-slate-200/60')
  ('bg-slate-700/30','bg-slate-200/30')
  ('bg-slate-700','bg-slate-200')
  ('bg-slate-600/20','bg-slate-300/20')
  ('bg-slate-600/30','bg-slate-300/30')
  ('bg-slate-600','bg-slate-300')
  ('bg-slate-400','bg-slate-300')
  ('bg-slate-500/20','bg-slate-300/20')
  ('bg-slate-500','bg-slate-300')
  ('bg-gray-800','bg-slate-200')
  ("'rgba(13,20,36,0.95)'",'rgba(255,255,255,0.95)')
  ("'1px solid #1e2a44'",'1px solid #d4dde4')
  ("color: '#e2e8f0'",'color: #0f172a')
  ('hover:bg-slate-600/60','hover:border-slate-400/60')
  ('shadow-lg shadow-black/20','shadow-lg shadow-black/5')
  ('hover:bg-cyan-500/5','hover:bg-cyan-100/50')
  ('hover:bg-emerald-500/5','hover:bg-emerald-100/50')
  ('hover:bg-pink-500/5','hover:bg-pink-100/50')
  ('hover:bg-red-500/10','hover:bg-red-100/50')
  ('text-slate-300','text-port-text')
  ('text-slate-200','text-port-text')
  ('text-slate-400','text-port-muted')
  ('text-slate-500','text-port-muted')
  ('text-sm text-slate-300','text-sm text-port-text')
  ('text-xs text-slate-300','text-xs text-port-text')
  ('hover:text-slate-200','hover:text-port-text')
  ('hover:text-white','hover:text-port-text')
  ('hover:text-slate-300','hover:text-port-text')
  ('ring-cyan-500/30','ring-cyan-500/40')
  ('ring-amber-500/30','ring-amber-500/40')
  ('ring-emerald-500/30','ring-emerald-500/40')
  ('ring-rose-500/30','ring-rose-500/40')
    ('ring-slate-500/30','ring-slate-400')
)

# Status-badge / pill text colors (dark -> light-safe)
$statusFixes = @(
  ('bg-rose-500/20 text-rose-400','bg-rose-500/20 text-rose-700')
  ('bg-amber-500/20 text-amber-400','bg-amber-500/20 text-amber-700')
  ('bg-emerald-500/20 text-emerald-400','bg-emerald-500/20 text-emerald-700')
  ('bg-sky-500/20 text-sky-400','bg-sky-500/20 text-sky-700')
  ('bg-pink-500/20 text-pink-400','bg-pink-500/20 text-pink-700')
  ('bg-violet-500/20 text-violet-400','bg-violet-500/20 text-violet-700')
  ('bg-purple-500/20 text-purple-400','bg-purple-500/20 text-purple-700')
  ('bg-blue-500/20 text-blue-400','bg-blue-500/20 text-blue-700')
  ('bg-fuchsia-500/20 text-fuchsia-400','bg-fuchsia-500/20 text-fuchsia-700')
  ('bg-indigo-500/20 text-indigo-400','bg-indigo-500/20 text-indigo-700')
  ('bg-red-500/20 text-red-400','bg-red-500/20 text-red-700')
  ('bg-lime-500/20 text-lime-400','bg-lime-500/20 text-lime-700')
  ('bg-teal-500/20 text-teal-400','bg-teal-500/20 text-teal-700')
  ('bg-cyan-500/20 text-cyan-400','bg-cyan-500/20 text-cyan-700')
  ('bg-slate-500/20 text-slate-300','bg-slate-500/20 text-slate-600')
  ('bg-slate-500/20 text-slate-400','bg-slate-500/20 text-slate-600')
  ('bg-amber-500/15 text-amber-300','bg-amber-500/20 text-amber-700')
  ('bg-emerald-500/15 text-emerald-300','bg-emerald-500/20 text-emerald-700')
  ('bg-pink-500/15 text-pink-300','bg-pink-500/20 text-pink-700')
  ('bg-indigo-500/15 text-indigo-300','bg-indigo-500/20 text-indigo-700')
  ('bg-fuchsia-500/15 text-fuchsia-300','bg-fuchsia-500/20 text-fuchsia-700')
  ('bg-rose-500/15 text-rose-300','bg-rose-500/20 text-rose-700')
  ('bg-violet-500/15 text-violet-300','bg-violet-500/20 text-violet-700')
  ('bg-purple-500/15 text-purple-300','bg-purple-500/20 text-purple-700')
  ('bg-cyan-500/15 text-cyan-300','bg-cyan-500/20 text-cyan-700')
  ('bg-sky-500/15 text-sky-300','bg-sky-500/20 text-sky-700')
  ('bg-blue-500/15 text-blue-300','bg-blue-500/20 text-blue-700')
  ('bg-teal-500/15 text-teal-300','bg-teal-500/20 text-teal-700')
  ('bg-slate-500/20 text-slate-300','bg-slate-500/20 text-slate-600')
  ('bg-slate-400 text-slate-900','bg-slate-300 text-slate-800')
)

$allReplacements = $replacements + $statusFixes

foreach ($f in $files) {
  $path = Join-Path $root $f
  $content = [System.IO.File]::ReadAllText($path)
  foreach ($r in $allReplacements) {
    $content = $content -replace $r[0], $r[1]
  }
  # final safety: any stray bare text-slate-* -> theme vars
  $content = $content -replace 'text-slate-100','text-port-text'
  $content = $content -replace 'text-slate-200','text-port-text'
  $content = $content -replace 'text-slate-300','text-port-text'
  $content = $content -replace 'text-slate-400','text-port-muted'
  $content = $content -replace 'text-slate-500','text-port-muted'
  $content = $content -replace 'text-slate-600','text-port-muted'
  $content = $content -replace 'text-slate-700','text-port-muted'
  [System.IO.File]::WriteAllText($path, $content)
  Write-Host "Processed $f"
}