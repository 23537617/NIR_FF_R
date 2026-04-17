#!/bin/bash
export CORE_PEER_LOCALMSPID=Org1MSP
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/admin-msp

ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem
PEER0_ORG1_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/org1-tls-ca.crt
PEER0_ORG2_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/org2-tls-ca.crt

peer chaincode invoke -o orderer.example.com:7050 --waitForEvent --ordererTLSHostnameOverride orderer.example.com \
    --tls --cafile $ORDERER_CA -C npa-channel -n taskdocument \
    --peerAddresses peer0.org1.example.com:7051 --tlsRootCertFiles $PEER0_ORG1_CA \
    --peerAddresses peer0.org2.example.com:9051 --tlsRootCertFiles $PEER0_ORG2_CA \
    --certfile /etc/hyperledger/fabric/tls/server.crt --keyfile /etc/hyperledger/fabric/tls/server.key \
    -c '{"function":"approve_task","Args":["TASK_STATE_1"]}'