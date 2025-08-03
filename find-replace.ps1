# --- CONFIGURATION ---
# Set the starting directory for the search.
# "." means the current directory where the script is run.
$targetDirectory = "."

# Define the exact string to find.
$oldString = ".\forecast"

# Define the string to replace it with.
$newString = ".\forecast"

# Specify which file types to search in. Use "*.ext" format.
# Add or remove extensions as needed. Use "*.*" to search all files.
$fileTypes = @("*.txt", "*.py", "*.json", "*.md", "*.ps1", "*.xml", "*.html", "*.css", "*.js")

# --- SCRIPT LOGIC ---
Write-Host "Starting find and replace operation..."
Write-Host "Searching in: $(Resolve-Path $targetDirectory)"
Write-Host "File types: $($fileTypes -join ', ')"
Write-Host "----------------------------------"

# Get all files matching the specified types, searching recursively.
# The -Force parameter includes hidden files. Remove it if not needed.
$filesToProcess = Get-ChildItem -Path $targetDirectory -Include $fileTypes -Recurse -File -Force

foreach ($file in $filesToProcess) {
    # Read the file's entire content as a single raw string.
    $content = Get-Content -Path $file.FullName -Raw -ErrorAction SilentlyContinue

    # !! THIS IS THE CORRECTED LINE !!
    # First, check if $content is not null (to handle empty files),
    # then check if it contains the string.
    if ($null -ne $content -and $content.Contains($oldString)) {
        Write-Host "Found string in '$($file.FullName)'. Replacing..." -ForegroundColor Yellow
        
        # Perform the replacement.
        $newContent = $content.Replace($oldString, $newString)
        
        # Write the new, modified content back to the original file.
        try {
            Set-Content -Path $file.FullName -Value $newContent -Force -NoNewline -ErrorAction Stop
            Write-Host " -> Successfully replaced content in '$($file.FullName)'." -ForegroundColor Green
        }
        catch {
            Write-Error " -> FAILED to write to file '$($file.FullName)'. Error: $_"
        }
    }
}

Write-Host "----------------------------------"
Write-Host "Script finished."