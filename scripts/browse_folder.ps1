param(
    [string]$InitialFolder = "$env:USERPROFILE\Documents\gemini-projects"
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

$form = New-Object System.Windows.Forms.Form
$form.TopMost = $true
$form.ShowInTaskbar = $false
$form.Opacity = 0
$form.Size = New-Object System.Drawing.Size(1, 1)
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
$form.WindowState = [System.Windows.Forms.FormWindowState]::Normal
$form.Show()
$form.Visible = $false

$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = "Sélectionnez le dossier de travail (Workspace) pour Agy Studio"
if (Test-Path $InitialFolder) {
    $dialog.SelectedPath = $InitialFolder
}
$dialog.ShowNewFolderButton = $true

$result = $dialog.ShowDialog($form)
$form.Close()
$form.Dispose()

if ($result -eq [System.Windows.Forms.DialogResult]::OK -and (Test-Path $dialog.SelectedPath)) {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Write-Output $dialog.SelectedPath
}
