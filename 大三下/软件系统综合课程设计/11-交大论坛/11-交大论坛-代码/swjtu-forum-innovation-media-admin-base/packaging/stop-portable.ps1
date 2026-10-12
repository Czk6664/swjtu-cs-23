$ports = @(8080, 4173)
foreach ($port in $ports) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop
        foreach ($pid in ($connections | Select-Object -ExpandProperty OwningProcess -Unique)) {
            try {
                $proc = Get-Process -Id $pid -ErrorAction Stop
                if ($proc.ProcessName -match '^(java|javaw)$') {
                    Stop-Process -Id $pid -Force
                    Write-Host "Stopped $($proc.ProcessName) PID $pid on port $port"
                }
            } catch { }
        }
    } catch {
        Write-Host "Port $port is not occupied."
    }
}
