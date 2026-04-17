$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "Подготовка контейнера для тестов..."
Write-Host "=========================================="

# 1. Избавляемся от проблемы \r\n (Windows Line Endings) копируя скрипт на лету
$shContent = Get-Content .\verify_features.sh -Raw
$shContent = $shContent -replace "`r`n", "`n"
Set-Content -Path ".\temp_features.sh" -Value $shContent -Encoding ascii

# 2. Копируем сам скрипт в контейнер
docker cp .\temp_features.sh peer0.org1.example.com:/tmp/verify_features.sh
Remove-Item -Force .\temp_features.sh

# 3. Копируем Admin MSP (чтобы у пользователя peer1 были админские права)
$ADMIN_MSP = ".\organizations\peerOrganizations\org1.example.com\users\Admin@org1.example.com\msp"
if (Test-Path $ADMIN_MSP) {
    docker exec peer0.org1.example.com rm -rf /etc/hyperledger/fabric/admin-msp
    docker exec peer0.org1.example.com mkdir -p /etc/hyperledger/fabric/admin-msp
    
    # Копируем содержимое директории
    docker cp "$ADMIN_MSP\." peer0.org1.example.com:/tmp/temp-msp
    docker exec peer0.org1.example.com bash -c "cp -r /tmp/temp-msp/* /etc/hyperledger/fabric/admin-msp/"
    docker exec peer0.org1.example.com rm -rf /tmp/temp-msp
    
    # Если нет config.yaml - берем его с уровня выше
    $ORG_CONFIG = ".\organizations\peerOrganizations\org1.example.com\msp\config.yaml"
    if (Test-Path $ORG_CONFIG) {
        docker cp $ORG_CONFIG peer0.org1.example.com:/etc/hyperledger/fabric/admin-msp/config.yaml
    }
}

Write-Host "-> Запуск тестов внутри Linux контейнера (для обхода ошибок парсинга Windows)...."
docker exec peer0.org1.example.com bash /tmp/verify_features.sh
