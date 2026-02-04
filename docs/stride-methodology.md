# Metodologia STRIDE

## O que é STRIDE?

STRIDE é uma metodologia de **modelagem de ameaças** criada pela **Microsoft** em 1999. O nome é um acrônimo para seis categorias de ameaças de segurança.

## As 6 Categorias

| Categoria | Ameaça | Propriedade Violada | Pergunta-chave |
|-----------|--------|---------------------|----------------|
| **S**poofing | Falsificação de Identidade | Autenticação | Alguém pode fingir ser outro usuário ou sistema? |
| **T**ampering | Adulteração de Dados | Integridade | Dados podem ser modificados sem autorização? |
| **R**epudiation | Repúdio | Não-repúdio | Um usuário pode negar ter realizado uma ação? |
| **I**nformation Disclosure | Vazamento de Informações | Confidencialidade | Informações sensíveis podem ser expostas? |
| **D**enial of Service | Negação de Serviço | Disponibilidade | O sistema pode ser derrubado ou ficar lento? |
| **E**levation of Privilege | Escalação de Privilégios | Autorização | Alguém pode obter permissões que não deveria ter? |

## Por que usar STRIDE?

### 1. Cobertura Sistemática
STRIDE garante que você analise **todos os tipos de ameaças** para cada componente. Sem uma metodologia, é fácil esquecer categorias inteiras de ataques.

### 2. Padrão da Indústria
- Criada pela Microsoft, usada há 25+ anos
- Adotada por empresas como Google, Amazon, Netflix
- Reconhecida por frameworks de segurança (NIST, ISO 27001)
- Exigida em certificações (PCI-DSS, SOC 2)

### 3. Linguagem Comum
Permite que desenvolvedores, arquitetos e equipes de segurança falem a mesma língua sobre ameaças.

### 4. Acionável
Cada categoria tem contramedidas conhecidas:

| Categoria | Contramedidas Típicas |
|-----------|----------------------|
| Spoofing | Autenticação forte (MFA, OAuth, certificados) |
| Tampering | Validação de entrada, checksums, assinaturas digitais |
| Repudiation | Logs de auditoria, timestamps, assinaturas |
| Information Disclosure | Criptografia, controle de acesso, mascaramento |
| Denial of Service | Rate limiting, WAF, auto-scaling, redundância |
| Elevation of Privilege | Princípio do menor privilégio, RBAC, validação de autorização |

### 5. Escala com Complexidade
Funciona tanto para uma API simples quanto para arquiteturas complexas com centenas de componentes.

## Como Aplicar STRIDE

### Processo Manual (Tradicional)

```
1. Desenhar diagrama de arquitetura
2. Identificar componentes e fluxos de dados
3. Para CADA componente:
   └── Para CADA categoria STRIDE:
       └── "Esta ameaça se aplica aqui?"
           └── Se sim: documentar + definir severidade + propor contramedida
4. Priorizar por severidade
5. Implementar contramedidas
```

**Problema:** Em um sistema com 20 componentes, são 120 análises manuais (20 × 6).

### Processo Automatizado (Threat Modeler AI)

```
1. Upload do diagrama de arquitetura
2. IA detecta componentes e conexões automaticamente
3. IA aplica STRIDE para cada componente
4. Resultado: relatório completo com ameaças priorizadas
```

**Vantagem:** Análise de 20 componentes em minutos, não horas.

## STRIDE vs Outras Metodologias

| Metodologia | Foco | Quando Usar |
|-------------|------|-------------|
| **STRIDE** | Ameaças por componente | Design de sistemas |
| **DREAD** | Priorização de riscos | Complemento ao STRIDE |
| **PASTA** | Processo completo de threat modeling | Projetos enterprise |
| **LINDDUN** | Privacidade | Sistemas com dados pessoais (LGPD/GDPR) |
| **OWASP Top 10** | Vulnerabilidades web | Aplicações web |

STRIDE é frequentemente combinada com DREAD para priorização:
- **D**amage (Dano)
- **R**eproducibility (Reprodutibilidade)
- **E**xploitability (Explorabilidade)
- **A**ffected Users (Usuários Afetados)
- **D**iscoverability (Descobribilidade)

## Exemplos Práticos

### Exemplo: API de Login

| STRIDE | Ameaça | Severidade | Contramedida |
|--------|--------|------------|--------------|
| Spoofing | Atacante usa credenciais roubadas | Alta | Implementar MFA |
| Tampering | Modificação de token JWT | Alta | Assinar tokens com chave forte |
| Repudiation | Usuário nega ter feito login | Média | Log de IPs e timestamps |
| Info Disclosure | Senha exposta em logs | Crítica | Nunca logar senhas |
| DoS | Brute force de senhas | Alta | Rate limiting + CAPTCHA |
| Elevation | Token de usuário vira admin | Crítica | Validar claims no backend |

### Exemplo: Banco de Dados RDS

| STRIDE | Ameaça | Severidade | Contramedida |
|--------|--------|------------|--------------|
| Spoofing | Conexão com credenciais vazadas | Alta | IAM Database Auth |
| Tampering | SQL Injection | Crítica | Prepared statements |
| Repudiation | DBA modifica dados sem rastro | Alta | Audit logs habilitados |
| Info Disclosure | Backup sem criptografia | Alta | Encryption at rest |
| DoS | Queries pesadas travam DB | Média | Query timeout + read replicas |
| Elevation | App user vira DBA | Crítica | Princípio do menor privilégio |

## Referências

- [Microsoft STRIDE](https://docs.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
- [OWASP Threat Modeling](https://owasp.org/www-community/Threat_Modeling)
- [NIST SP 800-154](https://csrc.nist.gov/publications/detail/sp/800-154/draft)
