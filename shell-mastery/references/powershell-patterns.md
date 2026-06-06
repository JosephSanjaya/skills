# PowerShell Enterprise Patterns

Master PowerShell's object-oriented paradigm for Windows and cloud automation.

## Table of Contents
- Object Pipeline Fundamentals
- Performance Hierarchy
- Parallel Execution
- Provider Architecture
- Error Handling
- Secure Credential Management
- Best Practices

## Object Pipeline Fundamentals

### Text Streams vs Object Pipelines

**Bash (text-based):**
```bash
# Parse text output
ps aux | grep firefox | awk '{print $2}' | xargs kill
```

**PowerShell (object-based):**
```powershell
# Work with objects directly
Get-Process firefox | Stop-Process
```

### Understanding the Pipeline

**Objects preserve structure:**
```powershell
# Get process objects
Get-Process | Where-Object { $_.CPU -gt 100 }

# Each object has properties and methods
$process = Get-Process -Name chrome
$process.Id           # Property
$process.Kill()       # Method
$process | Get-Member # See all members
```

**Pipeline passes objects:**
```powershell
# Each stage receives full objects
Get-Service |
    Where-Object { $_.Status -eq 'Running' } |
    Select-Object Name, DisplayName, StartType |
    Sort-Object Name |
    Format-Table -AutoSize
```

### Common Pipeline Patterns

**Filtering:**
```powershell
# Where-Object (alias: where, ?)
Get-Process | Where-Object { $_.WorkingSet -gt 100MB }
Get-Process | Where-Object WorkingSet -gt 100MB  # Simplified
Get-Process | ? WorkingSet -gt 100MB             # Alias
```

**Selecting:**
```powershell
# Select-Object (alias: select)
Get-Process | Select-Object Name, Id, CPU
Get-Process | Select-Object -First 10
Get-Process | Select-Object -Last 5
Get-Process | Select-Object -Unique Name
```

**Sorting:**
```powershell
# Sort-Object (alias: sort)
Get-Process | Sort-Object CPU -Descending
Get-Process | Sort-Object -Property @{Expression='CPU'; Descending=$true}, Name
```

**Grouping:**
```powershell
# Group-Object (alias: group)
Get-Process | Group-Object ProcessName
Get-Service | Group-Object Status
```

**Measuring:**
```powershell
# Measure-Object (alias: measure)
Get-Process | Measure-Object WorkingSet -Sum -Average -Maximum
Get-ChildItem | Measure-Object Length -Sum
```

## Performance Hierarchy

### 1. Language Features (Fastest)

**Direct language constructs:**
```powershell
# foreach statement (fastest)
$sum = 0
foreach ($item in $collection) {
    $sum += $item.Value
}

# if statement
if ($condition) {
    # Execute
}

# switch statement
switch ($value) {
    1 { "One" }
    2 { "Two" }
    default { "Other" }
}
```

### 2. .NET Methods (Fast)

**Direct .NET calls:**
```powershell
# Math operations
[Math]::Sqrt(16)
[Math]::Pow(2, 10)
[Math]::Round(3.14159, 2)

# String operations
[String]::Join(",", $array)
[String]::IsNullOrEmpty($str)

# File operations (streaming)
[System.IO.File]::ReadLines($path)
[System.IO.File]::WriteAllText($path, $content)

# DateTime
[DateTime]::Now
[DateTime]::Parse("2024-01-01")
```

### 3. Cmdlets and Pipeline (Slower)

**PowerShell cmdlets:**
```powershell
# Convenient but slower for large datasets
Get-Content $path
Where-Object { $_.Property -eq $value }
ForEach-Object { $_.Process() }
```

### Performance Comparison

```powershell
# Slow - Pipeline with ForEach-Object
Measure-Command {
    1..10000 | ForEach-Object { $_ * 2 }
}

# Fast - foreach statement
Measure-Command {
    $result = foreach ($i in 1..10000) { $i * 2 }
}

# Fastest - .NET method
Measure-Command {
    $result = [System.Linq.Enumerable]::Range(1, 10000) | 
        ForEach-Object { $_ * 2 }
}
```

### Optimization Examples

**File reading:**
```powershell
# Slow - Loads entire file into memory
$content = Get-Content large.txt

# Fast - Streaming with .NET
$content = [System.IO.File]::ReadLines("large.txt")

# Process line by line
foreach ($line in [System.IO.File]::ReadLines("large.txt")) {
    # Process $line
}
```

**String operations:**
```powershell
# Slow - Multiple string concatenations
$result = ""
foreach ($item in $items) {
    $result += $item + ","
}

# Fast - StringBuilder
$sb = [System.Text.StringBuilder]::new()
foreach ($item in $items) {
    [void]$sb.Append($item).Append(",")
}
$result = $sb.ToString()

# Fastest - Join
$result = [String]::Join(",", $items)
```

## Parallel Execution

### ForEach-Object -Parallel (PowerShell 7+)

**Basic usage:**
```powershell
# Process items in parallel
1..100 | ForEach-Object -Parallel {
    Start-Sleep -Seconds 1
    "Processed $_"
} -ThrottleLimit 10
```

**With variables:**
```powershell
$apiUrl = "https://api.example.com"
$servers = @("server1", "server2", "server3")

$servers | ForEach-Object -Parallel {
    # Use $using: to access outer scope variables
    $response = Invoke-RestMethod -Uri "$using:apiUrl/status/$_"
    [PSCustomObject]@{
        Server = $_
        Status = $response.status
    }
} -ThrottleLimit 5
```

**Error handling:**
```powershell
$results = 1..10 | ForEach-Object -Parallel {
    try {
        # Risky operation
        $result = Invoke-WebRequest "https://example.com/$_"
        [PSCustomObject]@{
            Id = $_
            Success = $true
            Data = $result
        }
    } catch {
        [PSCustomObject]@{
            Id = $_
            Success = $false
            Error = $_.Exception.Message
        }
    }
} -ThrottleLimit 5

# Check results
$results | Where-Object { -not $_.Success }
```

### Start-ThreadJob (In-Process Threads)

**Basic usage:**
```powershell
# Start thread jobs
$jobs = 1..10 | ForEach-Object {
    Start-ThreadJob -ScriptBlock {
        param($num)
        Start-Sleep -Seconds 1
        $num * 2
    } -ArgumentList $_
}

# Wait and collect results
$results = $jobs | Wait-Job | Receive-Job
$jobs | Remove-Job

# Display results
$results
```

**With functions:**
```powershell
function Process-Data {
    param($Data)
    # Process data
    Start-Sleep -Seconds 1
    $Data * 2
}

$jobs = 1..10 | ForEach-Object {
    Start-ThreadJob -ScriptBlock ${function:Process-Data} -ArgumentList $_
}

$results = $jobs | Wait-Job | Receive-Job
$jobs | Remove-Job
```

### Avoid Start-Job (Out-of-Process)

**Why avoid:**
```powershell
# DON'T - Creates new PowerShell process (very slow)
$job = Start-Job -ScriptBlock {
    # This runs in a separate powershell.exe process
    # Requires XML serialization/deserialization
    # 8x slower than ThreadJob
}
```

**When to use:**
- Need complete process isolation
- Running untrusted code
- Require different PowerShell version

### Performance Comparison

```powershell
# Measure sequential
Measure-Command {
    1..100 | ForEach-Object {
        Start-Sleep -Milliseconds 100
    }
} # ~10 seconds

# Measure ForEach-Object -Parallel
Measure-Command {
    1..100 | ForEach-Object -Parallel {
        Start-Sleep -Milliseconds 100
    } -ThrottleLimit 10
} # ~1 second

# Measure ThreadJob
Measure-Command {
    $jobs = 1..100 | ForEach-Object {
        Start-ThreadJob -ScriptBlock {
            Start-Sleep -Milliseconds 100
        }
    }
    $jobs | Wait-Job | Remove-Job
} # ~1.2 seconds

# Measure Start-Job (slow)
Measure-Command {
    $jobs = 1..10 | ForEach-Object {
        Start-Job -ScriptBlock {
            Start-Sleep -Milliseconds 100
        }
    }
    $jobs | Wait-Job | Remove-Job
} # ~8 seconds (for just 10 items!)
```

## Provider Architecture

### Understanding Providers

**List available providers:**
```powershell
Get-PSProvider
```

**Common providers:**
- **FileSystem** - Files and directories
- **Registry** - Windows registry
- **Certificate** - Certificate stores
- **Environment** - Environment variables
- **Variable** - PowerShell variables
- **Alias** - Command aliases
- **Function** - PowerShell functions

### FileSystem Provider

```powershell
# Navigate like a drive
Set-Location C:\
Get-ChildItem

# Create items
New-Item -Path C:\Temp\test.txt -ItemType File
New-Item -Path C:\Temp\folder -ItemType Directory

# Copy/Move/Remove
Copy-Item source.txt destination.txt
Move-Item old.txt new.txt
Remove-Item file.txt
```

### Registry Provider

```powershell
# Navigate registry
Set-Location HKLM:\Software
Get-ChildItem

# Read registry value
Get-ItemProperty -Path "HKLM:\Software\Microsoft\Windows\CurrentVersion" -Name ProgramFilesDir

# Create registry key
New-Item -Path "HKLM:\Software\MyApp"

# Set registry value
Set-ItemProperty -Path "HKLM:\Software\MyApp" -Name "Version" -Value "1.0"

# Remove registry key
Remove-Item -Path "HKLM:\Software\MyApp" -Recurse
```

### Certificate Provider

```powershell
# List certificates
Get-ChildItem Cert:\CurrentUser\My

# Find certificate
Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -like "*example.com*" }

# Export certificate
$cert = Get-ChildItem Cert:\CurrentUser\My | Select-Object -First 1
Export-Certificate -Cert $cert -FilePath cert.cer
```

### Environment Provider

```powershell
# List environment variables
Get-ChildItem Env:

# Get specific variable
$env:PATH
Get-Item Env:PATH

# Set environment variable
$env:MY_VAR = "value"
Set-Item -Path Env:MY_VAR -Value "value"

# Remove environment variable
Remove-Item Env:MY_VAR
```

### Variable Provider

```powershell
# List variables
Get-ChildItem Variable:

# Get variable
Get-Variable MyVar

# Set variable
Set-Variable -Name MyVar -Value "test"

# Remove variable
Remove-Variable MyVar
```

## Error Handling

### Strict Mode

```powershell
# Enable strict mode
Set-StrictMode -Version Latest

# Set error action preference
$ErrorActionPreference = 'Stop'  # Treat all errors as terminating
```

### Try-Catch-Finally

```powershell
try {
    # Risky operation
    $content = Get-Content "file.txt" -ErrorAction Stop
    
    # Process content
    $result = Process-Data $content
    
} catch [System.IO.FileNotFoundException] {
    Write-Error "File not found: $_"
    exit 1
    
} catch [System.UnauthorizedAccessException] {
    Write-Error "Access denied: $_"
    exit 1
    
} catch {
    Write-Error "Unexpected error: $_"
    Write-Error $_.ScriptStackTrace
    exit 1
    
} finally {
    # Always runs (cleanup)
    if ($tempFile) {
        Remove-Item $tempFile -ErrorAction SilentlyContinue
    }
}
```

### Error Action Preference

```powershell
# Per-command error action
Get-Content "file.txt" -ErrorAction Stop          # Terminate
Get-Content "file.txt" -ErrorAction SilentlyContinue  # Ignore
Get-Content "file.txt" -ErrorAction Continue      # Display and continue
Get-Content "file.txt" -ErrorAction Inquire       # Ask user

# Global preference
$ErrorActionPreference = 'Stop'
```

### Custom Error Messages

```powershell
function Get-UserData {
    param([string]$UserId)
    
    if ([string]::IsNullOrEmpty($UserId)) {
        throw "UserId cannot be null or empty"
    }
    
    $user = Get-ADUser $UserId -ErrorAction SilentlyContinue
    if (-not $user) {
        throw "User not found: $UserId"
    }
    
    return $user
}
```

## Secure Credential Management

### SecureString

```powershell
# Create SecureString
$securePassword = Read-Host "Enter password" -AsSecureString

# Convert to plain text (use carefully)
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
```

### PSCredential

```powershell
# Create credential
$username = "domain\user"
$password = Read-Host "Enter password" -AsSecureString
$credential = New-Object System.Management.Automation.PSCredential($username, $password)

# Use credential
Invoke-Command -ComputerName server01 -Credential $credential -ScriptBlock {
    Get-Process
}
```

### Credential Storage

```powershell
# Export credential (encrypted to current user)
$credential | Export-Clixml -Path credential.xml

# Import credential
$credential = Import-Clixml -Path credential.xml

# Use with commands
Connect-AzAccount -Credential $credential
```

### Azure Key Vault Integration

```powershell
# Install module
Install-Module -Name Az.KeyVault

# Connect to Azure
Connect-AzAccount

# Get secret
$secret = Get-AzKeyVaultSecret -VaultName "MyVault" -Name "DatabasePassword"
$secretValue = $secret.SecretValue

# Use secret
$credential = New-Object System.Management.Automation.PSCredential("username", $secretValue)
```

## Best Practices

### Parameter Validation

```powershell
function Process-File {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [ValidateScript({Test-Path $_})]
        [string]$Path,
        
        [Parameter(Mandatory=$false)]
        [ValidateRange(1, 100)]
        [int]$Timeout = 30,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet("Low", "Medium", "High")]
        [string]$Priority = "Medium"
    )
    
    # Function logic
}
```

### Comment-Based Help

```powershell
function Get-UserInfo {
    <#
    .SYNOPSIS
        Gets user information from Active Directory
    
    .DESCRIPTION
        Retrieves detailed user information including group memberships
        and last logon time
    
    .PARAMETER UserId
        The user ID to query
    
    .PARAMETER IncludeGroups
        Include group memberships in output
    
    .EXAMPLE
        Get-UserInfo -UserId "jdoe"
        
    .EXAMPLE
        Get-UserInfo -UserId "jdoe" -IncludeGroups
    
    .NOTES
        Requires Active Directory module
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$UserId,
        
        [switch]$IncludeGroups
    )
    
    # Function logic
}
```

### Output Objects

```powershell
# Return custom objects
function Get-SystemInfo {
    [PSCustomObject]@{
        ComputerName = $env:COMPUTERNAME
        OS = (Get-CimInstance Win32_OperatingSystem).Caption
        Memory = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
        Uptime = (Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
    }
}

# Use PSTypeName for consistent types
function Get-UserData {
    $obj = [PSCustomObject]@{
        PSTypeName = 'Custom.UserData'
        Name = "John Doe"
        Email = "john@example.com"
    }
    return $obj
}
```

### Logging

```powershell
function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [ValidateSet("Info", "Warning", "Error")]
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Write to console
    switch ($Level) {
        "Info" { Write-Host $logMessage -ForegroundColor Green }
        "Warning" { Write-Warning $logMessage }
        "Error" { Write-Error $logMessage }
    }
    
    # Write to file
    Add-Content -Path "script.log" -Value $logMessage
}

# Usage
Write-Log "Script started"
Write-Log "Warning: Using default configuration" -Level Warning
Write-Log "Error: Failed to connect" -Level Error
```

## Complete Example Script

```powershell
#Requires -Version 7.0

<#
.SYNOPSIS
    Process server health checks in parallel
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string[]]$Servers,
    
    [Parameter(Mandatory=$false)]
    [int]$ThrottleLimit = 10
)

# Strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "Info")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

try {
    Write-Log "Starting health checks for $($Servers.Count) servers"
    
    # Process in parallel
    $results = $Servers | ForEach-Object -Parallel {
        $server = $_
        
        try {
            # Check connectivity
            $ping = Test-Connection -ComputerName $server -Count 1 -Quiet
            
            if ($ping) {
                # Get system info
                $os = Get-CimInstance -ComputerName $server -ClassName Win32_OperatingSystem
                $cpu = Get-CimInstance -ComputerName $server -ClassName Win32_Processor
                
                [PSCustomObject]@{
                    Server = $server
                    Status = "Online"
                    OS = $os.Caption
                    Uptime = (Get-Date) - $os.LastBootUpTime
                    CPULoad = $cpu.LoadPercentage
                    MemoryFree = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
                }
            } else {
                [PSCustomObject]@{
                    Server = $server
                    Status = "Offline"
                }
            }
        } catch {
            [PSCustomObject]@{
                Server = $server
                Status = "Error"
                Error = $_.Exception.Message
            }
        }
    } -ThrottleLimit $ThrottleLimit
    
    # Display results
    $results | Format-Table -AutoSize
    
    # Export to CSV
    $results | Export-Csv -Path "health-check-$(Get-Date -Format 'yyyyMMdd-HHmmss').csv" -NoTypeInformation
    
    Write-Log "Health checks completed successfully"
    
} catch {
    Write-Log "Error: $_" -Level "Error"
    exit 1
}
```

## Remember

- **Objects > Text** - Leverage the object pipeline
- **Performance hierarchy** - Language > .NET > Cmdlets
- **Parallel for I/O** - Use ForEach-Object -Parallel or ThreadJob
- **Providers are powerful** - Navigate registry/certificates like files
- **Error handling is mandatory** - Use try-catch-finally
- **Secure credentials** - Never hardcode, use SecureString/KeyVault
- **Validate parameters** - Use [ValidateScript], [ValidateRange], etc.
- **Return objects** - Use [PSCustomObject] for structured output
