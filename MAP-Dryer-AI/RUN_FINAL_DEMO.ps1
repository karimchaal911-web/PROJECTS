param(
    [ValidateRange(1, 60)]
    [Alias("ReplaySeconds")]
    [int]$RefreshSeconds = 5,
    [ValidateRange(2, 60)]
    [int]$PageRefreshSeconds = 5,
    [switch]$Resume,
    [switch]$Windowed
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ============================================================================
# MAP-Dryer-AI — FINAL ONE-CLICK DEMO LAUNCHER
#
# Default behavior:
#   1) Uses realtime_pipeline/.env for DB/source/model configuration
#   2) Starts a FRESH demo by clearing only runtime demo tables
#   3) Forces the replay/inference cadence to 5 seconds
#   4) Forces Power BI automatic page refresh to 5 seconds
#   5) Starts realtime_service.py
#   6) Waits for the SQL/Power BI contract to become available
#   7) Opens the canonical .pbip dashboard
#   8) Presents the live report canvas borderless, like a PowerPoint show
#   9) Keeps the simulation alive until Power BI is closed
#
# Resume without clearing runtime tables:
#   .\RUN_FINAL_DEMO.ps1 -Resume
#
# Accelerated replay without overloading page rendering:
#   .\RUN_FINAL_DEMO.ps1 -ReplaySeconds 2
#
# Open in the normal Power BI editor instead of presentation mode:
#   .\RUN_FINAL_DEMO.ps1 -Windowed
#
# Page refresh remains 5 s unless explicitly overridden. A sub-5-second page
# refresh is possible, but it can overlap interactive page navigation because
# every DirectQuery visual on the active page refreshes together.
# ============================================================================

function Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Success([string]$Message) {
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Fail([string]$Message) {
    throw $Message
}

function Initialize-PowerBIPresentationSupport {
    if (-not ("MapDryerPresentationInterop" -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public struct MapDryerRect
{
    public int Left;
    public int Top;
    public int Right;
    public int Bottom;
    public int Width { get { return Right - Left; } }
    public int Height { get { return Bottom - Top; } }
}

[StructLayout(LayoutKind.Sequential)]
public struct MapDryerPoint
{
    public int X;
    public int Y;
}

[StructLayout(LayoutKind.Sequential)]
public struct MapDryerWindowPlacement
{
    public int length;
    public int flags;
    public int showCmd;
    public MapDryerPoint ptMinPosition;
    public MapDryerPoint ptMaxPosition;
    public MapDryerRect rcNormalPosition;
}

public sealed class MapDryerWindowSnapshot
{
    public IntPtr Handle;
    public IntPtr Style;
    public IntPtr ExtendedStyle;
    public MapDryerWindowPlacement Placement;
    public bool Active;
}

public static class MapDryerPresentationInterop
{
    private const int GWL_STYLE = -16;
    private const int GWL_EXSTYLE = -20;
    private const long WS_CAPTION = 0x00C00000L;
    private const long WS_THICKFRAME = 0x00040000L;
    private const long WS_MINIMIZEBOX = 0x00020000L;
    private const long WS_MAXIMIZEBOX = 0x00010000L;
    private const long WS_SYSMENU = 0x00080000L;
    private const long WS_EX_DLGMODALFRAME = 0x00000001L;
    private const long WS_EX_WINDOWEDGE = 0x00000100L;
    private const long WS_EX_CLIENTEDGE = 0x00000200L;
    private const long WS_EX_STATICEDGE = 0x00020000L;

    private const uint MONITOR_DEFAULTTONEAREST = 2;
    private const uint SWP_NOSIZE = 0x0001;
    private const uint SWP_NOMOVE = 0x0002;
    private const uint SWP_FRAMECHANGED = 0x0020;
    private const uint SWP_SHOWWINDOW = 0x0040;
    private const uint SWP_NOSENDCHANGING = 0x0400;
    private const int SW_RESTORE = 9;

    private static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
    private static readonly IntPtr HWND_NOTOPMOST = new IntPtr(-2);

    [StructLayout(LayoutKind.Sequential)]
    private struct MonitorInfo
    {
        public int cbSize;
        public MapDryerRect rcMonitor;
        public MapDryerRect rcWork;
        public uint dwFlags;
    }

    [DllImport("user32.dll")]
    private static extern bool IsWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool IsIconic(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    private static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    private static extern bool GetWindowRect(IntPtr hWnd, out MapDryerRect rect);

    [DllImport("user32.dll")]
    private static extern bool GetWindowPlacement(IntPtr hWnd, ref MapDryerWindowPlacement placement);

    [DllImport("user32.dll")]
    private static extern bool SetWindowPlacement(IntPtr hWnd, ref MapDryerWindowPlacement placement);

    [DllImport("user32.dll")]
    private static extern IntPtr MonitorFromWindow(IntPtr hWnd, uint flags);

    [DllImport("user32.dll")]
    private static extern bool GetMonitorInfo(IntPtr monitor, ref MonitorInfo info);

    [DllImport("user32.dll", EntryPoint = "GetWindowLong")]
    private static extern int GetWindowLong32(IntPtr hWnd, int index);

    [DllImport("user32.dll", EntryPoint = "GetWindowLongPtr")]
    private static extern IntPtr GetWindowLong64(IntPtr hWnd, int index);

    [DllImport("user32.dll", EntryPoint = "SetWindowLong")]
    private static extern int SetWindowLong32(IntPtr hWnd, int index, int value);

    [DllImport("user32.dll", EntryPoint = "SetWindowLongPtr")]
    private static extern IntPtr SetWindowLong64(IntPtr hWnd, int index, IntPtr value);

    [DllImport("user32.dll")]
    private static extern bool SetWindowPos(
        IntPtr hWnd, IntPtr insertAfter, int x, int y, int width, int height, uint flags);

    [DllImport("user32.dll")]
    private static extern short GetAsyncKeyState(int virtualKey);

    private static IntPtr GetWindowLongPtr(IntPtr hWnd, int index)
    {
        return IntPtr.Size == 8
            ? GetWindowLong64(hWnd, index)
            : new IntPtr(GetWindowLong32(hWnd, index));
    }

    private static void SetWindowLongPtr(IntPtr hWnd, int index, IntPtr value)
    {
        if (IntPtr.Size == 8)
            SetWindowLong64(hWnd, index, value);
        else
            SetWindowLong32(hWnd, index, value.ToInt32());
    }

    public static bool Prepare(IntPtr hWnd)
    {
        if (!IsWindow(hWnd)) return false;
        if (IsIconic(hWnd))
        {
            ShowWindowAsync(hWnd, SW_RESTORE);
            ShowWindow(hWnd, SW_RESTORE);
        }
        SetForegroundWindow(hWnd);
        return true;
    }

    public static bool IsMinimized(IntPtr hWnd)
    {
        return !IsWindow(hWnd) || IsIconic(hWnd);
    }

    public static MapDryerWindowSnapshot Begin(IntPtr hWnd)
    {
        if (!IsWindow(hWnd)) return null;

        var placement = new MapDryerWindowPlacement();
        placement.length = Marshal.SizeOf(typeof(MapDryerWindowPlacement));
        if (!GetWindowPlacement(hWnd, ref placement)) return null;

        var state = new MapDryerWindowSnapshot();
        state.Handle = hWnd;
        state.Style = GetWindowLongPtr(hWnd, GWL_STYLE);
        state.ExtendedStyle = GetWindowLongPtr(hWnd, GWL_EXSTYLE);
        state.Placement = placement;
        state.Active = true;

        long style = state.Style.ToInt64();
        style &= ~(WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU);
        long extended = state.ExtendedStyle.ToInt64();
        extended &= ~(WS_EX_DLGMODALFRAME | WS_EX_WINDOWEDGE | WS_EX_CLIENTEDGE | WS_EX_STATICEDGE);

        SetWindowLongPtr(hWnd, GWL_STYLE, new IntPtr(style));
        SetWindowLongPtr(hWnd, GWL_EXSTYLE, new IntPtr(extended));
        SetWindowPos(hWnd, HWND_TOPMOST, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED | SWP_SHOWWINDOW);
        SetForegroundWindow(hWnd);
        return state;
    }

    public static bool MoveTopmost(IntPtr hWnd, int x, int y, int width, int height)
    {
        if (!IsWindow(hWnd)) return false;
        bool result = SetWindowPos(hWnd, HWND_TOPMOST, x, y, width, height,
            SWP_FRAMECHANGED | SWP_SHOWWINDOW | SWP_NOSENDCHANGING);
        SetForegroundWindow(hWnd);
        return result;
    }

    public static bool Restore(MapDryerWindowSnapshot state)
    {
        if (state == null || !state.Active || !IsWindow(state.Handle)) return false;

        SetWindowLongPtr(state.Handle, GWL_STYLE, state.Style);
        SetWindowLongPtr(state.Handle, GWL_EXSTYLE, state.ExtendedStyle);
        SetWindowPos(state.Handle, HWND_NOTOPMOST, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED | SWP_SHOWWINDOW);

        var placement = state.Placement;
        placement.length = Marshal.SizeOf(typeof(MapDryerWindowPlacement));
        if (placement.showCmd == 2) placement.showCmd = 1;
        SetWindowPlacement(state.Handle, ref placement);
        SetForegroundWindow(state.Handle);
        state.Active = false;
        return true;
    }

    public static MapDryerRect WindowBounds(IntPtr hWnd)
    {
        MapDryerRect rect;
        GetWindowRect(hWnd, out rect);
        return rect;
    }

    public static MapDryerRect MonitorBounds(IntPtr hWnd)
    {
        IntPtr monitor = MonitorFromWindow(hWnd, MONITOR_DEFAULTTONEAREST);
        var info = new MonitorInfo();
        info.cbSize = Marshal.SizeOf(typeof(MonitorInfo));
        GetMonitorInfo(monitor, ref info);
        return info.rcMonitor;
    }

    public static bool IsKeyDown(int virtualKey)
    {
        return (GetAsyncKeyState(virtualKey) & 0x8000) != 0;
    }

    public static bool IsForeground(IntPtr hWnd)
    {
        return GetForegroundWindow() == hWnd;
    }
}
'@
    }

    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
}

function Get-PowerBIReportCanvasBounds([IntPtr]$Handle) {
    try {
        $root = [System.Windows.Automation.AutomationElement]::FromHandle($Handle)
        $condition = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::NameProperty,
            "Power BI Report"
        )
        $elements = $root.FindAll(
            [System.Windows.Automation.TreeScope]::Descendants,
            $condition
        )

        $best = $null
        $bestArea = 0
        for ($i = 0; $i -lt $elements.Count; $i++) {
            $element = $elements.Item($i)
            $bounds = $element.Current.BoundingRectangle
            $area = $bounds.Width * $bounds.Height
            $aspect = if ($bounds.Height -gt 0) { $bounds.Width / $bounds.Height } else { 0 }
            if ($bounds.Left -gt -10000 -and $bounds.Top -gt -10000 -and
                $bounds.Width -gt 600 -and $bounds.Height -gt 400 -and
                $element.Current.ClassName -like "visualContainerHost*" -and
                $aspect -gt 1.70 -and $aspect -lt 1.85 -and
                $area -gt $bestArea) {
                $best = $bounds
                $bestArea = $area
            }
        }

        if ($best) {
            return [pscustomobject]@{
                Left   = [int][Math]::Round($best.Left)
                Top    = [int][Math]::Round($best.Top)
                Width  = [int][Math]::Round($best.Width)
                Height = [int][Math]::Round($best.Height)
            }
        }
    }
    catch {
        return $null
    }

    return $null
}

function Dismiss-PowerBIPresentationObstructions([IntPtr]$Handle) {
    # Power BI can place editor-only notification bars over the report canvas
    # (for example the calculated-column notice and the visual-query tip).
    # Resolve the calculated-column session notice with its own Refresh now
    # action, then dismiss/collapse any remaining editor-only tips.
    try {
        $root = [System.Windows.Automation.AutomationElement]::FromHandle($Handle)
        $window = [MapDryerPresentationInterop]::WindowBounds($Handle)
        $all = $root.FindAll(
            [System.Windows.Automation.TreeScope]::Descendants,
            [System.Windows.Automation.Condition]::TrueCondition
        )
        $hasCalculatedColumnNotice = $false

        for ($i = 0; $i -lt $all.Count; $i++) {
            $element = $all.Item($i)
            $bounds = $element.Current.BoundingRectangle
            if ($element.Current.Name -like "*calculated columns need to be manually refreshed*" -and
                $bounds.Left -ge $window.Left -and
                $bounds.Top -ge ($window.Top + 45) -and
                $bounds.Top -le ($window.Top + 350)) {
                $hasCalculatedColumnNotice = $true
                break
            }
        }

        if ($hasCalculatedColumnNotice) {
            for ($i = 0; $i -lt $all.Count; $i++) {
                $element = $all.Item($i)
                $bounds = $element.Current.BoundingRectangle
                if ($element.Current.Name -eq "Refresh now" -and
                    $element.Current.ClassName -eq "action-button" -and
                    $bounds.Left -ge $window.Left -and
                    $bounds.Right -le $window.Right -and
                    $bounds.Top -ge ($window.Top + 45) -and
                    $bounds.Top -le ($window.Top + 350)) {
                    try {
                        $pattern = $element.GetCurrentPattern(
                            [System.Windows.Automation.InvokePattern]::Pattern
                        )
                        $pattern.Invoke()
                        Start-Sleep -Seconds 2
                    }
                    catch {
                        # The remaining obstruction pass can still collapse it.
                    }
                    break
                }
            }
        }
    }
    catch {
        # Continue with the generic obstruction pass below.
    }

    for ($pass = 1; $pass -le 3; $pass++) {
        try {
            $root = [System.Windows.Automation.AutomationElement]::FromHandle($Handle)
            $window = [MapDryerPresentationInterop]::WindowBounds($Handle)
            $all = $root.FindAll(
                [System.Windows.Automation.TreeScope]::Descendants,
                [System.Windows.Automation.Condition]::TrueCondition
            )
            $invoked = $false

            for ($i = 0; $i -lt $all.Count; $i++) {
                $element = $all.Item($i)
                $bounds = $element.Current.BoundingRectangle
                $name = $element.Current.Name
                $className = $element.Current.ClassName

                $isDismissTip = (
                    $name -eq "Don't show again" -and
                    $bounds.Left -ge $window.Left -and
                    $bounds.Right -le $window.Right -and
                    $bounds.Top -ge ($window.Top + 45) -and
                    $bounds.Top -le ($window.Top + 350)
                )
                $isTopNoticeClose = (
                    $name -eq "Close" -and
                    $className -eq "icon-button" -and
                    $bounds.Left -ge ($window.Right - 140) -and
                    $bounds.Top -ge ($window.Top + 45) -and
                    $bounds.Top -le ($window.Top + 350)
                )
                $isTopNoticeDismiss = (
                    $className -like "dismiss-button*" -and
                    $bounds.Left -ge ($window.Right - 140) -and
                    $bounds.Top -ge ($window.Top + 45) -and
                    $bounds.Top -le ($window.Top + 350)
                )

                if (-not ($isDismissTip -or $isTopNoticeClose -or $isTopNoticeDismiss)) {
                    continue
                }

                try {
                    $pattern = $element.GetCurrentPattern(
                        [System.Windows.Automation.InvokePattern]::Pattern
                    )
                    $pattern.Invoke()
                    $invoked = $true
                    Start-Sleep -Milliseconds 300
                    break
                }
                catch {
                    continue
                }
            }

            if (-not $invoked) {
                break
            }
        }
        catch {
            break
        }
    }
}

function Set-PowerBICleanPresentationView([IntPtr]$Handle) {
    $result = [pscustomobject]@{
        RibbonCollapsedByLauncher = $false
        FitToPageApplied          = $false
    }

    try {
        $root = [System.Windows.Automation.AutomationElement]::FromHandle($Handle)

        # Use Power BI's own compact ribbon before cropping the editor chrome.
        $ribbonCondition = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::AutomationIdProperty,
            "RibbonModeToggle"
        )
        $ribbonButtons = $root.FindAll(
            [System.Windows.Automation.TreeScope]::Descendants,
            $ribbonCondition
        )
        for ($i = 0; $i -lt $ribbonButtons.Count; $i++) {
            $button = $ribbonButtons.Item($i)
            try {
                $pattern = $button.GetCurrentPattern(
                    [System.Windows.Automation.ExpandCollapsePattern]::Pattern
                )
                if ($pattern.Current.ExpandCollapseState -eq
                    [System.Windows.Automation.ExpandCollapseState]::Expanded) {
                    $pattern.Collapse()
                    $result.RibbonCollapsedByLauncher = $true
                }
                break
            }
            catch {
                continue
            }
        }

        Start-Sleep -Milliseconds 300

        # Fit the 1600 x 900 report page to the presentation canvas.
        $fitCondition = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::AutomationIdProperty,
            "fitToPageButton"
        )
        $fitButtons = $root.FindAll(
            [System.Windows.Automation.TreeScope]::Descendants,
            $fitCondition
        )
        for ($i = 0; $i -lt $fitButtons.Count; $i++) {
            $button = $fitButtons.Item($i)
            try {
                $pattern = $button.GetCurrentPattern(
                    [System.Windows.Automation.InvokePattern]::Pattern
                )
                $pattern.Invoke()
                $result.FitToPageApplied = $true
                break
            }
            catch {
                continue
            }
        }
    }
    catch {
        Write-Warning "Power BI opened, but its clean-view controls were not available yet. The borderless canvas will still be attempted."
    }

    Start-Sleep -Milliseconds 500
    return $result
}

function Restore-PowerBIRibbon([IntPtr]$Handle, [bool]$Expand) {
    if (-not $Expand) {
        return
    }

    try {
        $root = [System.Windows.Automation.AutomationElement]::FromHandle($Handle)
        $condition = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::AutomationIdProperty,
            "RibbonModeToggle"
        )
        $buttons = $root.FindAll(
            [System.Windows.Automation.TreeScope]::Descendants,
            $condition
        )
        for ($i = 0; $i -lt $buttons.Count; $i++) {
            try {
                $pattern = $buttons.Item($i).GetCurrentPattern(
                    [System.Windows.Automation.ExpandCollapsePattern]::Pattern
                )
                if ($pattern.Current.ExpandCollapseState -eq
                    [System.Windows.Automation.ExpandCollapseState]::Collapsed) {
                    $pattern.Expand()
                }
                break
            }
            catch {
                continue
            }
        }
    }
    catch {
        # Window restoration matters more than restoring the ribbon preference.
    }
}

function Enter-PowerBIPresentation([System.Diagnostics.Process]$Process) {
    Initialize-PowerBIPresentationSupport

    $handle = [IntPtr]$Process.MainWindowHandle
    if ($handle -eq [IntPtr]::Zero -or -not [MapDryerPresentationInterop]::Prepare($handle)) {
        Write-Warning "Power BI presentation mode could not acquire the report window."
        return $false
    }

    Start-Sleep -Milliseconds 500
    if ([MapDryerPresentationInterop]::IsMinimized($handle)) {
        Write-Warning "Power BI is minimized and could not be restored for presentation mode. Restore the dashboard once, then press F11."
        return $false
    }

    Dismiss-PowerBIPresentationObstructions -Handle $handle
    $cleanView = Set-PowerBICleanPresentationView -Handle $handle

    # Power BI can publish its titled window before the Chromium report canvas
    # is ready. Capture the editor-to-canvas insets before changing the native
    # window frame so presentation mode remains exact even if UI Automation is
    # briefly unavailable after the resize.
    $initialCanvas = $null
    for ($attempt = 1; $attempt -le 20; $attempt++) {
        $initialCanvas = Get-PowerBIReportCanvasBounds -Handle $handle
        if ($initialCanvas) {
            break
        }
        Start-Sleep -Milliseconds 500
    }

    $initialWindow = [MapDryerPresentationInterop]::WindowBounds($handle)
    $canvasInsets = $null
    if ($initialCanvas) {
        $canvasInsets = [pscustomobject]@{
            Left   = $initialCanvas.Left - $initialWindow.Left
            Top    = $initialCanvas.Top - $initialWindow.Top
            Right  = $initialWindow.Right - ($initialCanvas.Left + $initialCanvas.Width)
            Bottom = $initialWindow.Bottom - ($initialCanvas.Top + $initialCanvas.Height)
        }
    }

    $windowSnapshot = [MapDryerPresentationInterop]::Begin($handle)
    if (-not $windowSnapshot) {
        Restore-PowerBIRibbon -Handle $handle -Expand $cleanView.RibbonCollapsedByLauncher
        Write-Warning "Power BI presentation mode could not save the original window state."
        return $false
    }

    $script:PowerBIPresentationState = [pscustomobject]@{
        Process                   = $Process
        Handle                    = $handle
        WindowSnapshot            = $windowSnapshot
        RibbonCollapsedByLauncher = $cleanView.RibbonCollapsedByLauncher
    }

    $monitor = [MapDryerPresentationInterop]::MonitorBounds($handle)
    if ($canvasInsets) {
        [MapDryerPresentationInterop]::MoveTopmost(
            $handle,
            $monitor.Left - $canvasInsets.Left,
            $monitor.Top - $canvasInsets.Top,
            $monitor.Width + $canvasInsets.Left + $canvasInsets.Right,
            $monitor.Height + $canvasInsets.Top + $canvasInsets.Bottom
        ) | Out-Null
    }
    else {
        [MapDryerPresentationInterop]::MoveTopmost(
            $handle,
            $monitor.Left,
            $monitor.Top,
            $monitor.Width,
            $monitor.Height
        ) | Out-Null
    }
    Start-Sleep -Milliseconds 400

    # Align Power BI's live report canvas—not its editor window—to the exact
    # monitor rectangle. Fixed editor chrome is pushed just beyond the display,
    # leaving the interactive 16:9 report edge-to-edge like a slide show.
    $aligned = [bool]$canvasInsets
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        $canvas = Get-PowerBIReportCanvasBounds -Handle $handle
        if (-not $canvas) {
            Start-Sleep -Milliseconds 300
            continue
        }

        $window = [MapDryerPresentationInterop]::WindowBounds($handle)
        $deltaX = $monitor.Left - $canvas.Left
        $deltaY = $monitor.Top - $canvas.Top
        $deltaWidth = $monitor.Width - $canvas.Width
        $deltaHeight = $monitor.Height - $canvas.Height

        if ([Math]::Abs($deltaX) -le 2 -and
            [Math]::Abs($deltaY) -le 2 -and
            [Math]::Abs($deltaWidth) -le 2 -and
            [Math]::Abs($deltaHeight) -le 2) {
            $aligned = $true
            break
        }

        [MapDryerPresentationInterop]::MoveTopmost(
            $handle,
            $window.Left + $deltaX,
            $window.Top + $deltaY,
            [Math]::Max(800, $window.Width + $deltaWidth),
            [Math]::Max(600, $window.Height + $deltaHeight)
        ) | Out-Null
        Start-Sleep -Milliseconds 350
    }

    if (-not $aligned) {
        Write-Warning "Borderless mode is active, but exact report-canvas alignment could not be confirmed. Press F11 to restore the editor window."
    }

    [MapDryerPresentationInterop]::Prepare($handle) | Out-Null
    return $true
}

function Exit-PowerBIPresentation {
    if (-not $script:PowerBIPresentationState) {
        return
    }

    $state = $script:PowerBIPresentationState
    $script:PowerBIPresentationState = $null
    try {
        [MapDryerPresentationInterop]::Restore($state.WindowSnapshot) | Out-Null
        Start-Sleep -Milliseconds 400
        Restore-PowerBIRibbon `
            -Handle $state.Handle `
            -Expand $state.RibbonCollapsedByLauncher
    }
    catch {
        Write-Warning "Power BI closed before its editor window could be restored."
    }
}

function Find-BootstrapPython {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return $py.Source
    }

    Fail "Python was not found. Install Python 3 and rerun this launcher."
}

function Prepare-ProjectPython {
    $candidates = @(
        (Join-Path $ProjectRoot ".venv\Scripts\python.exe"),
        (Join-Path $ProjectRoot "venv\Scripts\python.exe"),
        (Join-Path $ProjectRoot "realtime_pipeline\.venv\Scripts\python.exe"),
        (Join-Path $ProjectRoot "realtime_pipeline\venv\Scripts\python.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $python = (Resolve-Path $candidate).Path
            & $python -c "import dotenv, joblib, numpy, pandas, psycopg, scipy, sklearn" 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $python
            }

            Step "Installing missing runtime dependencies into the project environment"
            & $python -m pip install -r (Join-Path $ProjectRoot "requirements.txt") -r (Join-Path $ProjectRoot "realtime_pipeline\requirements.txt")
            if ($LASTEXITCODE -ne 0) {
                Fail "Runtime dependencies could not be installed into $python."
            }
            return $python
        }
    }

    # No project venv exists. If the interpreter already on PATH satisfies the
    # runtime contract, use it rather than building and populating a new venv.
    $bootstrapPython = Find-BootstrapPython
    & $bootstrapPython -c "import dotenv, joblib, numpy, pandas, psycopg, scipy, sklearn" 2>$null
    if ($LASTEXITCODE -eq 0) {
        return $bootstrapPython
    }

    $venvRoot = Join-Path $ProjectRoot ".venv"
    Step "Creating the project Python environment"
    & $bootstrapPython -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) {
        Fail "Could not create the project virtual environment at $venvRoot."
    }

    $python = Join-Path $venvRoot "Scripts\python.exe"
    & $python -m pip install -r (Join-Path $ProjectRoot "requirements.txt") -r (Join-Path $ProjectRoot "realtime_pipeline\requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        Fail "Runtime dependencies could not be installed into $venvRoot."
    }
    return $python
}

function Patch-PowerBIRefresh([int]$Seconds) {
    $pagesRoot = Join-Path $PowerBIReportRoot "definition\pages"
    if (-not (Test-Path $pagesRoot)) {
        Fail "Power BI pages folder was not found: $pagesRoot"
    }

    $pageFiles = Get-ChildItem -Path $pagesRoot -Filter "page.json" -Recurse -File
    if (-not $pageFiles) {
        Fail "No Power BI page.json files were found."
    }

    # Power BI has emitted two page-refresh serialization families. Named APR
    # pages use an ISO duration such as 'PT5S'; numeric refresh-type pages use
    # a numeric literal such as 5D. Preserve the page's existing family rather
    # than creating a mixed configuration that Desktop silently ignores.
    $durationPattern = '(?s)(?<prefix>"duration"\s*:\s*\{.*?"Value"\s*:\s*")(?<current>\d+D|''PT\d+S''|PT\d+S)(?<suffix>")'
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)

    $matched = 0
    $changed = 0

    foreach ($file in $pageFiles) {
        $text = [System.IO.File]::ReadAllText($file.FullName)

        if ($text -notmatch '"pageRefresh"') {
            continue
        }

        $usesNamedApr = $text -match '(?s)"refreshType"\s*:\s*\{.*?"Value"\s*:\s*"''APR''"'
        $durationValue = if ($usesNamedApr) { "'PT${Seconds}S'" } else { "${Seconds}D" }
        $expectedDuration = '(?s)"duration"\s*:\s*\{.*?"Value"\s*:\s*"' + [Regex]::Escape($durationValue) + '"'
        $durationEvaluator = [System.Text.RegularExpressions.MatchEvaluator]{
            param([System.Text.RegularExpressions.Match]$match)
            $match.Groups["prefix"].Value + $durationValue + $match.Groups["suffix"].Value
        }

        $newText = [System.Text.RegularExpressions.Regex]::Replace(
            $text, $durationPattern, $durationEvaluator
        )

        if ($newText -ne $text) {
            [System.IO.File]::WriteAllText($file.FullName, $newText, $utf8NoBom)
            $changed++
        }

        if ($newText -match $expectedDuration) {
            $matched++
        }
    }

    if ($matched -eq 0) {
        Fail "Could not confirm a ${Seconds}-second automatic page refresh in the Power BI page definitions."
    }

    Success "Power BI automatic page refresh confirmed at ${Seconds}s on $matched page(s)."
}

function Reset-DemoTables {
    Step "Resetting runtime demo tables for a clean presentation replay"

    $env:MAP_DRYER_ENV_PATH = $EnvFile

    $resetCode = @'
import os
from dotenv import load_dotenv
import psycopg

env_path = os.environ["MAP_DRYER_ENV_PATH"]
load_dotenv(env_path, override=True)

required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
missing = [k for k in required if not os.getenv(k)]
if missing:
    raise RuntimeError("Missing DB settings in realtime_pipeline/.env: " + ", ".join(missing))

with psycopg.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            TRUNCATE TABLE
                public.dryer_abnormal_variables,
                public.dryer_model_outputs,
                public.dryer_map
            RESTART IDENTITY CASCADE;
        """)
print("Runtime demo tables cleared.")
'@

    $resetCode | & $PythonExe -
    if ($LASTEXITCODE -ne 0) {
        Fail "Could not reset runtime demo tables. Verify PostgreSQL and realtime_pipeline/.env."
    }

    Success "Runtime demo tables reset. Datasets and model files were NOT touched."
}

function Test-RuntimeInputs {
    $env:MAP_DRYER_ENV_PATH = $EnvFile
    $env:MAP_DRYER_PIPELINE_ROOT = Split-Path -Parent $EnvFile

    $checkCode = @'
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(os.environ["MAP_DRYER_ENV_PATH"])
pipeline_root = Path(os.environ["MAP_DRYER_PIPELINE_ROOT"])
load_dotenv(env_path, override=False)

source = Path(os.environ.get("SOURCE_CSV_5S", "../resources/dashboard_demo/MAP_Dryer_Dashboard_Demo_5s.csv"))
warmup = Path(os.environ.get("WARMUP_CSV_5S", "../resources/dashboard_demo/MAP_Dryer_Dashboard_Warmup_5s.csv"))
models = Path(os.environ.get("MODELS_5S_DIR", "../models/5s"))
if not source.is_absolute():
    source = (pipeline_root / source).resolve()
if not warmup.is_absolute():
    warmup = (pipeline_root / warmup).resolve()
if not models.is_absolute():
    models = (pipeline_root / models).resolve()

required = [
    source,
    warmup,
    models / "quality_moisture_pipeline.joblib",
    models / "anomaly_model.joblib",
    models / "anomaly_scaler.joblib",
    models / "feature_schema.json",
    models / "reference_profile.json",
]
missing = [str(path) for path in required if not path.is_file()]
if missing:
    raise FileNotFoundError("Missing required runtime files:\n- " + "\n- ".join(missing))
print(f"Replay source: {source}")
print(f"Hidden warm-up: {warmup}")
print(f"Model directory: {models}")
'@

    $checkCode | & $PythonExe -
    if ($LASTEXITCODE -ne 0) {
        Fail "Runtime input validation failed. Restore the dashboard demo source/model artifact named above and rerun."
    }
    Success "Dashboard demo source and final model artifacts are available."
}

# ---------------------------- Resolve project -------------------------------

$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = (Get-Location).Path
}

$RealtimeScript   = Join-Path $ProjectRoot "realtime_pipeline\src\realtime_service.py"
$VerifyScript     = Join-Path $ProjectRoot "realtime_pipeline\src\verify_powerbi_views.py"
$BootstrapScript  = Join-Path $ProjectRoot "realtime_pipeline\src\apply_sql_migration.py"
$EnvFile          = Join-Path $ProjectRoot "realtime_pipeline\.env"
$PowerBIDir       = Join-Path $ProjectRoot "POWERBI DASHBOARD"
$PowerBIReportRoot = Join-Path $PowerBIDir "MAP Dryer AI Dashboard.Report"

foreach ($requiredPath in @($RealtimeScript, $EnvFile, $PowerBIDir)) {
    if (-not (Test-Path $requiredPath)) {
        Fail "Required project path not found: $requiredPath`nPlace RUN_FINAL_DEMO.ps1 in the MAP-Dryer-AI repository root."
    }
}

$PreferredPBIP = Join-Path $PowerBIDir "MAP Dryer AI Dashboard.pbip"
if (Test-Path $PreferredPBIP) {
    $PowerBIProject = $PreferredPBIP
}
else {
    $PowerBIProject = Get-ChildItem -Path $PowerBIDir -Filter "*.pbip" -File |
        Where-Object { $_.Name -notmatch '(?i)backup|old|test|draft' } |
        Select-Object -First 1 -ExpandProperty FullName
}

if (-not $PowerBIProject) {
    Fail "No canonical .pbip Power BI project was found in '$PowerBIDir'."
}

$PythonExe = Prepare-ProjectPython

Write-Host ""
Write-Host "============================================================" -ForegroundColor DarkGreen
Write-Host " MAP DRYER AI — FINAL 5-SECOND DEMO" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor DarkGreen
Write-Host "Project : $ProjectRoot"
Write-Host "Python  : $PythonExe"
Write-Host "Power BI: $PowerBIProject"
Write-Host "Replay  : $RefreshSeconds seconds per source row"
Write-Host "Display : $PageRefreshSeconds seconds per page refresh"
Write-Host "Mode    : $(if ($Resume) { 'RESUME' } else { 'FRESH REPLAY' })"

# Do not modify PBIR files while Desktop has them open.
$existingPBI = Get-Process "PBIDesktop" -ErrorAction SilentlyContinue
if ($existingPBI) {
    Fail "Power BI Desktop is already open. Save/close it first, then rerun this launcher so the 5-second page-refresh setting can be applied safely."
}

# ---------------------------- Python sanity --------------------------------

Step "Checking Python"
& $PythonExe --version
if ($LASTEXITCODE -ne 0) {
    Fail "Python could not be executed."
}
Success "Python is available."

# ---------------------------- Environment ----------------------------------

Step "Preparing final 5-second replay settings"

# Remove stale shell-level project settings so realtime_service.py gets its
# DB/source/model configuration from realtime_pipeline/.env.
foreach ($name in @(
    "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
    "SOURCE_CSV_5S", "WARMUP_CSV_5S", "SOURCE_PARTITION_5S", "REPLAY_START_TIMESTAMP",
    "MODELS_5S_DIR"
)) {
    Remove-Item "Env:$name" -ErrorAction SilentlyContinue
}

# Runtime overrides for THIS launcher only.
$env:PYTHONUTF8 = "1"
# Unbuffered so realtime_pipeline/logs/final_demo_runtime.*.log stay
# readable while the service runs and survive a forced stop.
$env:PYTHONUNBUFFERED = "1"
$env:POLL_INTERVAL_SECONDS = [string]$RefreshSeconds
$env:REPLAY_INTERVAL_SECONDS = [string]$RefreshSeconds
$env:REPLAY_SPEED = "1"
$env:MAX_CYCLES = "0"
$env:EXIT_WHEN_EXHAUSTED = "true"
$env:CONTINUOUS_DEMO_MODE = "false"
$env:STALE_AFTER_SECONDS = [string]([Math]::Max(30, $RefreshSeconds * 6))
$env:REPLAY_FROM_START = if ($Resume) { "false" } else { "true" }

Success "Runtime cadence set to ${RefreshSeconds}s."

if ($PageRefreshSeconds -lt 5) {
    Write-Warning "A ${PageRefreshSeconds}s page refresh can make navigation laggy because every active-page DirectQuery visual refreshes together. Keep PageRefreshSeconds at 5 for smooth presentation mode."
}

Step "Validating dashboard demonstration replay and final model artifacts"
Test-RuntimeInputs

# ---------------------------- Power BI refresh -----------------------------

Step "Configuring Power BI for ${PageRefreshSeconds}-second DirectQuery page refresh"
Patch-PowerBIRefresh -Seconds $PageRefreshSeconds

# ---------------------------- Fresh/Resume DB -------------------------------

if (-not $Resume) {
    try {
        Reset-DemoTables
    }
    catch {
        # If the database/schema has never been initialized, bootstrap once.
        if (Test-Path $BootstrapScript) {
            Write-Warning "Initial reset failed. Attempting the existing database bootstrap once..."
            & $PythonExe $BootstrapScript
            if ($LASTEXITCODE -ne 0) {
                throw
            }
            Reset-DemoTables
        }
        else {
            throw
        }
    }
}
else {
    Success "Resume mode selected: existing runtime rows were preserved."
}

# ---------------------------- Start service --------------------------------

$ServiceProcess = $null
$script:PowerBIPresentationState = $null
$LogDir = Join-Path $ProjectRoot "realtime_pipeline\logs"
$ServiceStdout = Join-Path $LogDir "final_demo_runtime.stdout.log"
$ServiceStderr = Join-Path $LogDir "final_demo_runtime.stderr.log"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

try {
    Step "Starting the realtime inference/replay service"

    $ServiceProcess = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList @("`"$RealtimeScript`"") `
        -WorkingDirectory $ProjectRoot `
        -RedirectStandardOutput $ServiceStdout `
        -RedirectStandardError $ServiceStderr `
        -PassThru

    Start-Sleep -Seconds 2
    $ServiceProcess.Refresh()

    if ($ServiceProcess.HasExited) {
        $details = if (Test-Path $ServiceStderr) { Get-Content $ServiceStderr -Raw } else { "No stderr log was produced." }
        $serviceExitCode = $ServiceProcess.ExitCode
        Fail ("The realtime service exited immediately with code {0}`n{1}" -f $serviceExitCode, $details)
    }

    Success ("Realtime service started (PID {0})" -f $ServiceProcess.Id)

    # ------------------------ Wait for SQL contract -------------------------

    if (Test-Path $VerifyScript) {
        Step "Waiting for PostgreSQL / Power BI views to become ready"

        $ready = $false
        $maxAttempts = 18   # about 90 seconds max
        $verifyLog = Join-Path $env:TEMP "map_dryer_verify_powerbi.txt"

        for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
            Start-Sleep -Seconds 5

            $ServiceProcess.Refresh()
            if ($ServiceProcess.HasExited) {
                Fail "The realtime service stopped during startup with code $($ServiceProcess.ExitCode)."
            }

            & $PythonExe $VerifyScript *> $verifyLog
            if ($LASTEXITCODE -eq 0) {
                $ready = $true
                break
            }

            Write-Host "   Waiting for first data/view readiness... ($attempt/$maxAttempts)"
        }

        if ($ready) {
            Success "PostgreSQL / Power BI view verification passed."
        }
        else {
            $details = if (Test-Path $verifyLog) { Get-Content $verifyLog -Raw } else { "No verifier log was produced." }
            Fail "Power BI SQL views did not become ready within 90 seconds.`n$details"
        }
    }
    else {
        Write-Warning "verify_powerbi_views.py was not found; skipping the optional readiness check."
        Start-Sleep -Seconds 8
    }

    # ----------------------------- Open PBI ---------------------------------

    Step "Opening the final Power BI dashboard"
    Start-Process -FilePath $PowerBIProject | Out-Null

    # The Microsoft Store build starts through a short-lived PBIDesktop.exe
    # before handing the PBIP to the real report window. Track the titled
    # window, not that temporary process, or the runtime stops during loading.
    $DashboardTitle = [System.IO.Path]::GetFileNameWithoutExtension($PowerBIProject)
    $PowerBIProcess = $null
    for ($i = 1; $i -le 90; $i++) {
        Start-Sleep -Seconds 2
        $PowerBIProcess = Get-Process "PBIDesktop" -ErrorAction SilentlyContinue |
            Where-Object { $_.MainWindowTitle -like "*$DashboardTitle*" } |
            Sort-Object StartTime |
            Select-Object -First 1

        if ($PowerBIProcess) {
            break
        }

        if ($i % 5 -eq 0) {
            Write-Host "   Power BI is loading the dashboard... ($($i * 2)s)"
        }
    }

    if (-not $PowerBIProcess) {
        Fail "Power BI Desktop did not open '$DashboardTitle' within 180 seconds."
    }

    # Make the completed report visible instead of leaving it behind the
    # launcher/VS Code after the Store-app process handoff.
    try {
        $Shell = New-Object -ComObject WScript.Shell
        $null = $Shell.AppActivate($PowerBIProcess.Id)
    }
    catch {
        Write-Warning "The dashboard opened but could not be brought to the foreground automatically."
    }

    $PresentationSupportReady = $false
    try {
        Initialize-PowerBIPresentationSupport
        $PresentationSupportReady = $true
    }
    catch {
        Write-Warning "PowerPoint-style presentation mode is unavailable: $($_.Exception.Message)"
    }

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor DarkGreen
    Write-Host " DEMO RUNNING" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor DarkGreen
    Write-Host "• Runtime inserts one observation approximately every ${RefreshSeconds}s."
    Write-Host "• Power BI DirectQuery pages refresh approximately every ${PageRefreshSeconds}s."
    Write-Host "• The dashboard is the existing canonical .pbip project."
    if ($Windowed) {
        Write-Host "• Windowed editor mode requested. Press F11 while Power BI is active to present."
    }
    else {
        Write-Host "• PowerPoint-style full screen starts automatically."
    }
    Write-Host "• F11 toggles presentation mode; Esc exits full screen."
    Write-Host "• Close Power BI to stop the simulation automatically."
    Write-Host "• Or press Ctrl+C in this launcher."
    Write-Host ""

    Success ("Power BI dashboard opened (PID {0})" -f $PowerBIProcess.Id)

    if ($PresentationSupportReady -and -not $Windowed) {
        if (Enter-PowerBIPresentation -Process $PowerBIProcess) {
            Success "Power BI report canvas is running edge-to-edge in presentation mode."
        }
    }

    # Follow the titled report window rather than one PID. This remains valid
    # if Power BI performs another internal process handoff. The shorter poll
    # also makes F11/Esc presentation controls feel immediate without changing
    # the five-second DirectQuery page-refresh cadence.
    $F11WasDown = $false
    $EscapeWasDown = $false
    $nextWindowCheck = [DateTime]::UtcNow
    $missingSince = $null

    while ($true) {
        if ($PresentationSupportReady) {
            $F11Down = [MapDryerPresentationInterop]::IsKeyDown(0x7A)
            $EscapeDown = [MapDryerPresentationInterop]::IsKeyDown(0x1B)
            $activeHandle = if ($script:PowerBIPresentationState) {
                $script:PowerBIPresentationState.Handle
            }
            else {
                [IntPtr]$PowerBIProcess.MainWindowHandle
            }
            $PowerBIIsForeground = [MapDryerPresentationInterop]::IsForeground($activeHandle)

            if ($F11Down -and -not $F11WasDown -and $PowerBIIsForeground) {
                if ($script:PowerBIPresentationState) {
                    Exit-PowerBIPresentation
                }
                else {
                    $PowerBIProcess.Refresh()
                    Enter-PowerBIPresentation -Process $PowerBIProcess | Out-Null
                }
            }

            if ($EscapeDown -and -not $EscapeWasDown -and
                $PowerBIIsForeground -and $script:PowerBIPresentationState) {
                Exit-PowerBIPresentation
            }

            $F11WasDown = $F11Down
            $EscapeWasDown = $EscapeDown
        }

        if ([DateTime]::UtcNow -ge $nextWindowCheck) {
            $OpenDashboard = Get-Process "PBIDesktop" -ErrorAction SilentlyContinue |
                Where-Object { $_.MainWindowTitle -like "*$DashboardTitle*" } |
                Select-Object -First 1

            if (-not $OpenDashboard) {
                if (-not $missingSince) {
                    $missingSince = [DateTime]::UtcNow
                }
                elseif (([DateTime]::UtcNow - $missingSince).TotalSeconds -ge 3) {
                    break
                }
            }
            else {
                $missingSince = $null
            }

            $nextWindowCheck = [DateTime]::UtcNow.AddSeconds(1)
        }

        Start-Sleep -Milliseconds 75
    }
}
finally {
    if ($script:PowerBIPresentationState) {
        Exit-PowerBIPresentation
    }

    if ($ServiceProcess) {
        try {
            $ServiceProcess.Refresh()
            if (-not $ServiceProcess.HasExited) {
                Step "Stopping realtime simulation"
                Stop-Process -Id $ServiceProcess.Id -Force -ErrorAction SilentlyContinue
                Success "Realtime service stopped."
            }
        }
        catch {
            # Nothing else to clean up.
        }
    }

    Remove-Item Env:MAP_DRYER_ENV_PATH -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Demo finished." -ForegroundColor Green
