[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+$')]
    [string]$Repository,
    [ValidateSet('private', 'public')]
    [string]$Visibility = 'private',
    [switch]$CreateRepository
)

$ErrorActionPreference = 'Stop'
function Invoke-Checked {
    param([string]$Program, [string[]]$ArgumentList)
    & $Program @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Program (exit $LASTEXITCODE)"
    }
}

$taskRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $taskRoot
try {
    Get-Command git, gh -ErrorAction Stop | Out-Null
    Invoke-Checked -Program gh -ArgumentList @('auth', 'status')
    $currentBranch = (Invoke-Checked -Program git -ArgumentList @('branch', '--show-current')).Trim()
    if ($currentBranch -ne 'solution') {
        throw 'Switch to the solution branch before publishing.'
    }
    $changes = Invoke-Checked -Program git -ArgumentList @('status', '--porcelain')
    if ($changes) { throw 'Commit or save pending changes before publishing.' }
    $plan = Get-Content -LiteralPath 'docs/pr-plan.json' -Raw -Encoding UTF8 | ConvertFrom-Json
    $remoteNames = @(Invoke-Checked -Program git -ArgumentList @('remote'))
    $remoteUrl = "https://github.com/$Repository.git"
    if ($remoteNames -contains 'origin') {
        $existing = (Invoke-Checked -Program git -ArgumentList @('remote', 'get-url', 'origin')).Trim()
        $accepted = @($remoteUrl, "https://github.com/$Repository", "git@github.com:$Repository.git")
        if ($accepted -notcontains $existing) {
            throw 'origin points to another repository; review the remote manually.'
        }
    }
    if ($CreateRepository) {
        # Intentionally fails if the repository already exists. Do not use this
        # switch for an existing repository; no README or unrelated history is created.
        Invoke-Checked -Program gh -ArgumentList @('repo', 'create', $Repository, "--$Visibility")
    } else {
        Invoke-Checked -Program gh -ArgumentList @('repo', 'view', $Repository, '--json', 'nameWithOwner')
    }
    if ($remoteNames -notcontains 'origin') {
        Invoke-Checked -Program git -ArgumentList @('remote', 'add', 'origin', $remoteUrl)
    }
    $references = @('main', 'solution', 'refs/tags/baseline') + @($plan | ForEach-Object { $_.branch })
    Invoke-Checked -Program git -ArgumentList (@('push', 'origin') + $references)
    $links = @()
    foreach ($item in $plan) {
        $existingJson = Invoke-Checked -Program gh -ArgumentList @(
            'pr', 'list', '--repo', $Repository, '--head', $item.branch,
            '--base', $item.base, '--state', 'all', '--json', 'url'
        )
        $existingPRs = @($existingJson | ConvertFrom-Json)
        if ($existingPRs.Count -gt 0) {
            $url = $existingPRs[0].url
        } else {
            $url = Invoke-Checked -Program gh -ArgumentList @(
                'pr', 'create', '--repo', $Repository, '--head', $item.branch,
                '--base', $item.base, '--title', $item.title,
                '--body-file', $item.body_file
            )
        }
        $links += [PSCustomObject]@{ id = $item.id; url = "$url".Trim() }
        New-Item -ItemType Directory -Path 'artifacts' -Force | Out-Null
        $links | ConvertTo-Json | Set-Content -LiteralPath 'artifacts/pull-requests.json' -Encoding UTF8
        Write-Output "$($item.id): $url"
    }
    Write-Output 'Published. Pull request URLs are saved in artifacts/pull-requests.json.'
} finally {
    Pop-Location
}
