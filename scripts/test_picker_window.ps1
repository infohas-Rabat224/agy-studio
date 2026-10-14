Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;

public class Win32WindowInspector {
    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

    public const uint WM_CLOSE = 0x0010;
    public const uint WM_SYSCOMMAND = 0x0112;
    public const uint SC_CLOSE = 0xF060;
}
"@

Write-Host "[1] Starting AgyStudioFolderPicker.exe --dialog..."
$proc = Start-Process -FilePath "C:\Agy Studio\AgyStudioFolderPicker.exe" -ArgumentList '--dialog "C:\Agy Studio"' -PassThru -NoNewWindow

Start-Sleep -Milliseconds 1200

$targetPid = [uint32]$proc.Id
Write-Host "[2] Target PID is $targetPid"

$foundWindows = [System.Collections.Generic.List[psobject]]::new()

$enumProc = [Win32WindowInspector+EnumWindowsProc]{
    param($hwnd, $lparam)
    $pidVal = [uint32]0
    [Win32WindowInspector]::GetWindowThreadProcessId($hwnd, [ref]$pidVal) | Out-Null
    if ($pidVal -eq $script:targetPid) {
        $sbTitle = New-Object System.Text.StringBuilder 512
        [Win32WindowInspector]::GetWindowText($hwnd, $sbTitle, $sbTitle.Capacity) | Out-Null
        $title = $sbTitle.ToString()

        $sbClass = New-Object System.Text.StringBuilder 256
        [Win32WindowInspector]::GetClassName($hwnd, $sbClass, $sbClass.Capacity) | Out-Null
        $cls = $sbClass.ToString()

        $foundWindows.Add([PSCustomObject]@{
            Hwnd = $hwnd
            Title = $title
            Class = $cls
        })
    }
    return $true
}

[Win32WindowInspector]::EnumWindows($enumProc, [IntPtr]::Zero) | Out-Null

Write-Host "[3] Windows found for PID $($targetPid): $($foundWindows.Count)"
foreach ($w in $foundWindows) {
    Write-Host "   HWND: $($w.Hwnd) | Class: '$($w.Class)' | Title: '$($w.Title)'"
}

if ($foundWindows.Count -gt 0) {
    Write-Host "[4] Closing dialog window via SC_CLOSE..."
    foreach ($w in $foundWindows) {
        [Win32WindowInspector]::PostMessage($w.Hwnd, [Win32WindowInspector]::WM_SYSCOMMAND, [IntPtr][Win32WindowInspector]::SC_CLOSE, [IntPtr]::Zero) | Out-Null
        [Win32WindowInspector]::PostMessage($w.Hwnd, [Win32WindowInspector]::WM_CLOSE, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
    }
}

$proc.WaitForExit(3000) | Out-Null
Write-Host "[5] Process exited with code: $($proc.ExitCode)"
