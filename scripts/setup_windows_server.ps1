#Requires -RunAsAdministrator
# SIEM TCC - Setup Windows Server 2022 para banca (rodar 1x como Admin)

Write-Host "=== SIEM TCC - Setup Windows Server ===" -ForegroundColor Cyan

# 1. Auditoria Logon (sem isso 0 eventos 4625)
Write-Host "[*] Habilitando auditoria de logon..." -ForegroundColor Yellow
auditpol /set /category:"Logon/Logoff" /success:enable /failure:enable | Out-Null
auditpol /get /category:"Logon/Logoff"

# 2. RDP
Write-Host "[*] Liberando RDP..." -ForegroundColor Yellow
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -Name fDenyTSConnections -Value 0 -Force
Enable-NetFirewallRule -DisplayGroup "Remote Desktop" | Out-Null

# 3. Firewall SIEM (5001) + SMB (445 para teste Kali)
Write-Host "[*] Liberando firewall 5001 e 445..." -ForegroundColor Yellow
if (-not (Get-NetFirewallRule -DisplayName "SIEM 5001" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName "SIEM 5001" -Direction Inbound -LocalPort 5001 -Protocol TCP -Action Allow | Out-Null
}
if (-not (Get-NetFirewallRule -DisplayName "SIEM SMB" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName "SIEM SMB" -Direction Inbound -LocalPort 445 -Protocol TCP -Action Allow | Out-Null
}

# 4. Usuario alvo para brute force (nao use Administrator direto)
Write-Host "[*] Criando usuario victima..." -ForegroundColor Yellow
$pass = ConvertTo-SecureString "Victima123!" -AsPlainText -Force
if (-not (Get-LocalUser -Name "victima" -ErrorAction SilentlyContinue)) {
    New-LocalUser -Name "victima" -Password $pass -FullName "Alvo TCC" -Description "Conta alvo para teste Kali" | Out-Null
    Add-LocalGroupMember -Group "Remote Desktop Users" -Member "victima"
    Add-LocalGroupMember -Group "Users" -Member "victima"
    Write-Host "[V] Usuario victima criado: Victima123!" -ForegroundColor Green
} else {
    Set-LocalUser -Name "victima" -Password $pass
    Write-Host "[V] Usuario victima ja existe - senha resetada" -ForegroundColor Green
}

Write-Host "`n=== Setup concluido ===" -ForegroundColor Green
Write-Host "1. Teste: auditpol /get /category:""Logon/Logoff"" (deve ser Success and Failure)"
Write-Host "2. Teste Kali: nmap -p 3389,445,5001 10.0.2.10"
Write-Host "3. Rode o SIEM como Admin: python app.py"
pause