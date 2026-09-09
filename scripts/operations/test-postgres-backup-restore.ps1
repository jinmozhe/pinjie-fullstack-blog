param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDatabase,
    [Parameter(Mandatory = $true)]
    [string]$RestoreDatabase,
    [Parameter(Mandatory = $true)]
    [string]$Username,
    [Parameter(Mandatory = $true)]
    [string]$ConfirmSourceDatabase,
    [Parameter(Mandatory = $true)]
    [string]$ConfirmRestoreDatabase,
    [string]$DatabaseHost = "127.0.0.1",
    [ValidateRange(1, 65535)]
    [int]$Port = 5432,
    [string]$MaintenanceDatabase = "postgres",
    [switch]$KeepRestoreDatabase
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-SafeDatabaseName {
    param(
        [string]$Name,
        [string]$ParameterName
    )
    if ($Name -notmatch '^[a-z][a-z0-9_]*_test$') {
        throw "$ParameterName must use lowercase letters, digits, underscores, and end with _test."
    }
}

function Get-PostgresTool {
    param([string]$Name)
    $command = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        throw "Required PostgreSQL tool is unavailable: $Name"
    }
    return $command.Source
}

function Invoke-PostgresTool {
    param(
        [string]$Tool,
        [string[]]$Arguments
    )
    & $Tool @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL tool failed with exit code ${LASTEXITCODE}: $([System.IO.Path]::GetFileName($Tool))"
    }
}

function Invoke-PsqlLines {
    param(
        [string]$Database,
        [string]$Sql
    )
    $arguments = @(
        "--no-password",
        "--no-psqlrc",
        "--set=ON_ERROR_STOP=1",
        "--tuples-only",
        "--no-align",
        "--host=$DatabaseHost",
        "--port=$Port",
        "--username=$Username",
        "--dbname=$Database",
        "--command=$Sql"
    )
    $output = & $script:Psql @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "psql validation failed for database '$Database'."
    }
    return @($output | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Get-DatabaseExists {
    param([string]$Name)
    $result = @(Invoke-PsqlLines -Database $MaintenanceDatabase -Sql "SELECT 1 FROM pg_database WHERE datname = '$Name';")
    return $result.Count -eq 1 -and $result[0] -eq "1"
}

function Get-DatabaseSnapshot {
    param([string]$Database)
    $tables = @(Invoke-PsqlLines -Database $Database -Sql "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;")
    if ($tables.Count -eq 0) {
        throw "Database '$Database' has no public tables to validate."
    }
    $rowCounts = [ordered]@{}
    foreach ($table in $tables) {
        if ($table -notmatch '^[a-z_][a-z0-9_]*$') {
            throw "Unsafe table name returned by PostgreSQL: $table"
        }
        $count = @(Invoke-PsqlLines -Database $Database -Sql "SELECT COUNT(*) FROM public.`"$table`";")
        if ($count.Count -ne 1 -or $count[0] -notmatch '^\d+$') {
            throw "Unable to read row count for public.$table in database '$Database'."
        }
        $rowCounts[$table] = [long]$count[0]
    }
    $revision = @(Invoke-PsqlLines -Database $Database -Sql "SELECT version_num FROM alembic_version ORDER BY version_num;")
    if ($revision.Count -ne 1) {
        throw "Database '$Database' must contain exactly one Alembic revision."
    }
    $constraintCount = @(Invoke-PsqlLines -Database $Database -Sql "SELECT COUNT(*) FROM pg_constraint WHERE connamespace = 'public'::regnamespace;")
    $invalidConstraints = @(Invoke-PsqlLines -Database $Database -Sql "SELECT COUNT(*) FROM pg_constraint WHERE connamespace = 'public'::regnamespace AND NOT convalidated;")
    return [pscustomobject]@{
        Tables = @($tables)
        RowCounts = $rowCounts
        Revision = $revision[0]
        ConstraintCount = [long]$constraintCount[0]
        InvalidConstraintCount = [long]$invalidConstraints[0]
    }
}

if ($DatabaseHost -notin @("127.0.0.1", "localhost", "::1")) {
    throw "Recovery drills are restricted to a local PostgreSQL host."
}
Assert-SafeDatabaseName -Name $SourceDatabase -ParameterName "SourceDatabase"
Assert-SafeDatabaseName -Name $RestoreDatabase -ParameterName "RestoreDatabase"
if ($SourceDatabase -eq $RestoreDatabase) {
    throw "SourceDatabase and RestoreDatabase must be different."
}
if ($ConfirmSourceDatabase -cne $SourceDatabase -or $ConfirmRestoreDatabase -cne $RestoreDatabase) {
    throw "Both confirmation values must exactly match their database names."
}

$script:Psql = Get-PostgresTool -Name "psql"
$pgDump = Get-PostgresTool -Name "pg_dump"
$pgRestore = Get-PostgresTool -Name "pg_restore"
$createDb = Get-PostgresTool -Name "createdb"
$dropDb = Get-PostgresTool -Name "dropdb"
$backupPath = Join-Path ([System.IO.Path]::GetTempPath()) ("pinjie-postgres-recovery-" + [guid]::NewGuid().ToString("N") + ".dump")
$restoreCreated = $false
$startedAt = Get-Date

try {
    if (-not (Get-DatabaseExists -Name $SourceDatabase)) {
        throw "Source test database does not exist: $SourceDatabase"
    }
    if (Get-DatabaseExists -Name $RestoreDatabase) {
        throw "Restore target already exists and will not be overwritten: $RestoreDatabase"
    }

    $sourceSnapshot = Get-DatabaseSnapshot -Database $SourceDatabase
    Invoke-PostgresTool -Tool $pgDump -Arguments @(
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--host=$DatabaseHost",
        "--port=$Port",
        "--username=$Username",
        "--file=$backupPath",
        $SourceDatabase
    )
    $backup = Get-Item -LiteralPath $backupPath
    if ($backup.Length -le 0) {
        throw "pg_dump produced an empty backup file."
    }

    Invoke-PostgresTool -Tool $createDb -Arguments @(
        "--host=$DatabaseHost",
        "--port=$Port",
        "--username=$Username",
        "--owner=$Username",
        $RestoreDatabase
    )
    $restoreCreated = $true
    Invoke-PostgresTool -Tool $pgRestore -Arguments @(
        "--exit-on-error",
        "--no-owner",
        "--no-privileges",
        "--host=$DatabaseHost",
        "--port=$Port",
        "--username=$Username",
        "--dbname=$RestoreDatabase",
        $backupPath
    )

    $restoredSnapshot = Get-DatabaseSnapshot -Database $RestoreDatabase
    if ($sourceSnapshot.Revision -cne $restoredSnapshot.Revision) {
        throw "Alembic revision differs after restore."
    }
    if (($sourceSnapshot.Tables -join "|") -cne ($restoredSnapshot.Tables -join "|")) {
        throw "Public table inventory differs after restore."
    }
    if ($sourceSnapshot.ConstraintCount -ne $restoredSnapshot.ConstraintCount) {
        throw "Constraint count differs after restore."
    }
    if ($restoredSnapshot.InvalidConstraintCount -ne 0) {
        throw "Restored database contains unvalidated constraints."
    }
    foreach ($table in $sourceSnapshot.Tables) {
        if ($sourceSnapshot.RowCounts[$table] -ne $restoredSnapshot.RowCounts[$table]) {
            throw "Row count differs after restore for public.$table."
        }
    }

    $totalRows = ($sourceSnapshot.RowCounts.Values | Measure-Object -Sum).Sum
    $duration = (Get-Date) - $startedAt
    Write-Host "PostgreSQL backup and restore drill passed."
    Write-Host "Revision: $($sourceSnapshot.Revision)"
    Write-Host "Tables: $($sourceSnapshot.Tables.Count); rows: $totalRows; constraints: $($sourceSnapshot.ConstraintCount)"
    Write-Host "Backup bytes: $($backup.Length); elapsed seconds: $([math]::Round($duration.TotalSeconds, 2))"
} finally {
    if ($restoreCreated -and -not $KeepRestoreDatabase) {
        Invoke-PostgresTool -Tool $dropDb -Arguments @(
            "--if-exists",
            "--host=$DatabaseHost",
            "--port=$Port",
            "--username=$Username",
            $RestoreDatabase
        )
    }
    if (Test-Path -LiteralPath $backupPath -PathType Leaf) {
        Remove-Item -LiteralPath $backupPath -Force
    }
}
