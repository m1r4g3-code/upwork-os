# Usage: powershell -File scripts\save_clip.ps1 v2-wf-01-master.png
# Take a snip (Win+Shift+S), then run this with the target filename.

param([string]$filename)

if (-not $filename) {
    Write-Host "Usage: powershell -File scripts\save_clip.ps1 <filename.png>"
    exit 1
}

Add-Type -AssemblyName System.Windows.Forms
$img = [System.Windows.Forms.Clipboard]::GetImage()

if ($img) {
    $out = Join-Path "C:\Users\HomePC\Documents\Upwork OS\outputs\assets" $filename
    $img.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Host "Saved: $out"
} else {
    Write-Host "No image in clipboard. Take a snip first (Win+Shift+S), then re-run."
}
