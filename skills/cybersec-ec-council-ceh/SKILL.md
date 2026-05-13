---
name: cybersec-ec-council-ceh
description: EC-Council CEH v13 — 20 modulos de ethical hacking, 5 fases (Reconnaissance, Scanning, Gaining Access, Maintaining Access, Clearing Tracks), 220+ labs, 3500+ tools. AI-powered attacks, cloud/IoT/OT, APTs. Framework 4-fases: Learn, Certify, Engage, Compete.
---

# CEH v13 - Certified Ethical Hacker

## Framework 5 Fases (Ataque)

| Fase | Tecnicas | Tools |
|------|----------|-------|
| **1. Reconnaissance** | OSINT pasivo/activo, footprint dominio, DNS enum, WHOIS, social media intel | recon-ng, Maltego, theHarvester, shodan |
| **2. Scanning** | Port scan, vuln scan, network mapping, banner grab | nmap, masscan, nessus, openvas |
| **3. Gaining Access** | Exploit web (SQLi, XSS, CSRF), buffer overflow, password attacks, social eng | metasploit, sqlmap, hydra, hashcat, BeEF |
| **4. Maintaining Access** | Backdoors, rootkits, C2 channels, persistence (registry, scheduled tasks, services) | meterpreter, empire, covenant, sliver |
| **5. Clearing Tracks** | Log deletion, anti-forensics, MAC time stomping, file shredding | meterpreter clearev, BleachBit, secure-delete |

## 20 Modulos CEH v13

1. Intro to Ethical Hacking | 2. Footprinting & Recon | 3. Scanning Networks | 4. Enumeration
5. Vuln Analysis | 6. System Hacking | 7. Malware Threats | 8. Sniffing
9. Social Engineering | 10. DoS/DDoS | 11. Session Hijacking | 12. IDS/Firewall/Honeypot evasion
13. Hacking Web Servers | 14. Web Apps | 15. SQL Injection | 16. Wireless
17. Mobile | 18. IoT/OT | 19. Cloud Computing | 20. Cryptography

## AI-driven attacks (v13 nuevo)

- Prompt injection en LLMs
- Deepfake social eng
- AI-generated malware (polimorfico)
- Adversarial ML attacks

## Como reportar evidencia (CEH style)

```
1. Executive Summary (riesgo en lenguaje business)
2. Scope & Methodology (que se probo, que no)
3. Findings por severidad (CVSS 3.1)
4. Evidence (screenshots, command outputs, PCAPs)
5. Remediation (con timeline)
6. Appendix: TTP mapping (MITRE ATT&CK)
```

## Para defender mi empresa

- Implementar el reverso de cada modulo como control defensivo
- Red team interno o externo cada Q
- Blue team con KPIs: MTTD, MTTR, MTTC

Source: eccouncil.org/cehv13-brochure/
