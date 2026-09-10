# Graph Engineering com Neo4j em projetos Spec-Driven

## Visão geral

A proposta é usar o **Neo4j como uma camada de engenharia** sobre o repositório.

O código, as specs, ADRs, testes e histórico Git continuam sendo a **source of truth**.  
O Neo4j apenas cria uma representação conectada dessas informações para permitir consultas que seriam difíceis de fazer apenas com arquivos.

Em vez de enxergar o projeto como uma coleção de documentos:

```text
spec.md
plan.md
tasks.md
ADR-012.md
permissions.ts
rbac.e2e.ts
PR #97
```

passamos a enxergá-lo como um grafo:

```text
Requirement
    ↓
Spec
    ↓
Task
   ↙   ↘
Code   Test
  ↑
 PR
```

Isso permite responder perguntas como:

- O que será afetado se este ADR mudar?
- Quais tarefas já podem ser executadas?
- Quais tarefas podem rodar em paralelo?
- Dois agentes provavelmente vão editar os mesmos arquivos?
- Esta spec possui implementação e testes?
- Este PR implementa qual requirement?
- Qual é o contexto mínimo que um agente precisa para executar uma tarefa?

---

# 1. O problema que estamos resolvendo

Em projetos Spec-Driven, normalmente acumulamos:

- requirements;
- specs;
- planos;
- tasks;
- ADRs;
- código;
- testes;
- pull requests;
- commits;
- agentes;
- worktrees.

O problema é que esses artefatos geralmente estão conectados apenas de forma implícita.

Um desenvolvedor entende que:

```text
ADR-012
    ↓
afeta RBAC
    ↓
afeta permissions.ts
    ↓
afeta ProtectedRoute
    ↓
exige testes E2E
```

Mas essa relação pode não existir de forma estruturada.

Um agente de IA precisa então:

1. procurar arquivos;
2. ler documentos grandes;
3. inferir relações;
4. descobrir dependências;
5. decidir o que é relevante;
6. torcer para não esquecer alguma coisa.

Com um Engineering Graph, essas relações passam a existir explicitamente.

---

# 2. Onde entra o Neo4j

O Neo4j **não faz parte da aplicação de negócio**.

Ele faz parte da toolchain de desenvolvimento.

```text
                    Git Repository
                  source of truth
                         │
                         ▼
                  Graph Sync Engine
                         │
                         ▼
                       Neo4j
                 Engineering Graph
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     Spec Kit          Agents             CI
        │                │                │
        ▼                ▼                ▼
    planning        context build     validations
    tasks           worktrees         drift checks
```

Isso traz uma vantagem importante:

> Se o Neo4j ficar indisponível, a aplicação continua funcionando.

O que perde capacidade temporariamente é o processo de engenharia.

---

# 3. Regra principal: Git continua sendo a source of truth

Não devemos escrever manualmente documentação diretamente no Neo4j.

O fluxo recomendado é:

```text
Markdown / YAML / Code / Git
            │
            ▼
      Graph Sync Engine
            │
            ▼
          Neo4j
```

Por exemplo, uma spec poderia continuar sendo um Markdown normal:

```yaml
---
id: SPEC-RBAC-001
type: spec
capability: CAP-RBAC
status: active

requires:
  - REQ-RBAC-01
  - REQ-RBAC-02

constrained_by:
  - ADR-012

depends_on:
  - SPEC-AUTH-001

implements:
  - src/auth/permissions.ts
  - src/components/Can.tsx

validated_by:
  - tests/rbac.unit.ts
  - tests/rbac.e2e.ts
---
```

O restante do arquivo continua legível por humanos:

```markdown
# RBAC

## Problema

Precisamos controlar funcionalidades disponíveis para cada perfil...

## Acceptance Criteria

...
```

O Graph Sync interpreta o frontmatter e atualiza o Neo4j.

---

# 4. Modelo inicial do grafo

Não precisamos modelar o universo inteiro na primeira versão.

Uma V1 pode funcionar com apenas sete tipos de nós.

## Nós

```text
Requirement
Spec
ADR
Task
CodeArtifact
Test
PullRequest
```

Exemplo:

```text
(:Requirement {id: "REQ-RBAC-01"})
(:Spec {id: "SPEC-RBAC-001"})
(:ADR {id: "ADR-012"})
(:Task {id: "TASK-RBAC-04"})
(:CodeArtifact {path: "src/auth/permissions.ts"})
(:Test {path: "tests/rbac.e2e.ts"})
(:PullRequest {number: 97})
```

---

# 5. Relacionamentos

Os relacionamentos são a parte mais importante.

Podemos começar com algo como:

```text
Requirement ──REALIZED_BY──────► Spec

Spec ─────────CONSTRAINED_BY───► ADR
Spec ─────────DECOMPOSED_INTO──► Task
Spec ─────────DEPENDS_ON────────► Spec

Task ─────────DEPENDS_ON────────► Task
Task ─────────IMPLEMENTED_BY────► CodeArtifact
Task ─────────VALIDATED_BY──────► Test

PullRequest ──IMPLEMENTS────────► Task
PullRequest ──CHANGES───────────► CodeArtifact
```

Visualmente:

```text
REQ-RBAC-01
     │
     ▼
SPEC-RBAC-001
     │
     ├────────────► ADR-012
     │
     ▼
TASK-RBAC-04
   │        │
   ▼        ▼
permissions.ts   rbac.e2e.ts
```

---

# 6. Caso prático: um ADR mudou

Imagine que alteramos:

```text
ADR-012
Capabilities tipadas + CASL encapsulado
```

Sem um grafo, um agente teria que procurar manualmente tudo relacionado ao RBAC.

Com Neo4j, fazemos uma travessia.

Exemplo conceitual:

```cypher
MATCH path =
  (adr:ADR {id: "ADR-012"})
  <-[*1..5]-
  (affected)

RETURN DISTINCT
  labels(affected),
  affected.id,
  length(path)

ORDER BY length(path);
```

Poderíamos descobrir:

```text
ADR-012
 │
 ├── SPEC-RBAC-001
 │     ├── TASK-RBAC-01
 │     │     └── src/auth/permissions.ts
 │     │
 │     ├── TASK-RBAC-02
 │     │     └── src/components/Can.tsx
 │     │
 │     └── TASK-RBAC-04
 │           ├── tests/rbac.unit.ts
 │           └── tests/rbac.e2e.ts
 │
 └── SPEC-ROUTING-004
       └── src/router/ProtectedRoute.tsx
```

O agente recebe somente o contexto relevante.

---

# 7. Contexto mínimo para agentes

Um dos maiores ganhos é reduzir context pollution.

Hoje podemos entregar ao agente:

```text
Leia:
- constitution.md
- spec.md
- plan.md
- tasks.md
- vários ADRs
- src/
- tests/
```

Com o Engineering Graph:

```text
TASK-RBAC-04
      │
      ▼
    Neo4j
      │
      ▼
relevant subgraph
      │
      ▼
 context package
      │
      ▼
 Claude / Codex
```

O pacote poderia conter:

```text
Task
  TASK-RBAC-04

Parent Spec
  SPEC-RBAC-001

Requirements
  REQ-RBAC-01
  REQ-RBAC-02

Architecture Decisions
  ADR-012

Dependencies
  CAP-AUTH

Likely Code
  src/auth/permissions.ts
  src/components/Can.tsx

Tests
  tests/rbac.unit.ts
  tests/rbac.e2e.ts
```

O agente começa o trabalho já sabendo onde está.

---

# 8. Tasks como DAG

No Spec-Driven Development, `/tasks` normalmente produz uma lista.

Mas tasks são naturalmente um **DAG — Directed Acyclic Graph**.

Exemplo:

```text
TASK-01 ────────────────┐
                        ▼
TASK-02 ──► TASK-04 ──► TASK-07

TASK-03 ──► TASK-05

TASK-06
```

O Neo4j consegue descobrir automaticamente quais tarefas estão prontas.

```text
READY

TASK-01
TASK-02
TASK-03
TASK-06
```

Enquanto:

```text
BLOCKED

TASK-04 → depende de TASK-02
TASK-05 → depende de TASK-03
TASK-07 → depende de TASK-04 e TASK-01
```

Uma query poderia ser:

```cypher
MATCH (t:Task)

WHERE t.status = "pending"

AND NOT EXISTS {
    MATCH (t)-[:DEPENDS_ON]->(dependency:Task)
    WHERE dependency.status <> "done"
}

RETURN t.id
ORDER BY t.priority;
```

---

# 9. Paralelização de agentes

Esse é um dos casos mais interessantes.

Imagine:

```text
TASK-101 → RBAC frontend
TASK-102 → Users API
TASK-103 → Dashboard widgets
TASK-104 → RBAC E2E
```

O grafo conhece dependências e arquivos afetados.

Então o planner pode gerar:

```text
Wave 1

Agent A
└── TASK-101

Agent B
└── TASK-102

Agent C
└── TASK-103


Wave 2

Agent D
└── TASK-104
    depende de TASK-101
```

O resultado é uma execução baseada no grafo em vez de uma simples tentativa de paralelizar tudo.

---

# 10. Detectando possíveis conflitos

Imagine:

```text
TASK-A
├── src/auth/auth-provider.ts
└── src/router.tsx

TASK-B
├── src/auth/auth-provider.ts
└── src/users/hooks.ts

TASK-C
└── src/dashboard/widgets.tsx
```

Há um possível conflito entre A e B.

```text
TASK-A ─────────────┐
                    ▼
        auth-provider.ts
                    ▲
TASK-B ─────────────┘


TASK-C
  │
  ▼
dashboard/widgets.tsx
```

Uma query pode detectar automaticamente arquivos compartilhados:

```cypher
MATCH
  (a:Task)-[:IMPLEMENTED_BY]->(artifact:CodeArtifact)
  <-[:IMPLEMENTED_BY]-(b:Task)

WHERE a.id < b.id
AND a.status = "pending"
AND b.status = "pending"

RETURN
  a.id,
  b.id,
  collect(artifact.id) AS overlappingArtifacts;
```

Resultado:

```text
TASK-A
TASK-B
shared:
  src/auth/auth-provider.ts
```

O orchestrator pode decidir:

```text
A + C → paralelo

B → depois de A
```

---

# 11. Pull Requests no grafo

Um Pull Request também pode virar um nó.

Exemplo:

```text
PR #97
 │
 ├──CHANGES────► permissions.ts
 │
 ├──CHANGES────► Can.tsx
 │
 └──CHANGES────► rbac.e2e.ts
 │
 └──IMPLEMENTS─► TASK-RBAC-04
```

Agora conseguimos caminhar:

```text
PR
 ↓
Task
 ↓
Spec
 ↓
Requirement
```

Isso permite responder automaticamente:

> O que este PR implementa?

E gerar descrições como:

```markdown
## Implements

SPEC-RBAC-001

### Requirements

- REQ-RBAC-01
- REQ-RBAC-02

### Tasks

- TASK-RBAC-04

### Architecture Decisions

- ADR-012

### Changed Artifacts

- src/auth/permissions.ts
- src/components/Can.tsx

### Validation

- tests/rbac.unit.ts
- tests/rbac.e2e.ts
```

---

# 12. Spec Drift

O Engineering Graph também pode funcionar como um mecanismo de validação arquitetural.

## Spec sem teste

```cypher
MATCH (s:Spec)

WHERE NOT EXISTS {
    MATCH
      (s)-[:DECOMPOSED_INTO]->(:Task)
         -[:VALIDATED_BY]->(:Test)
}

RETURN s.id;
```

## Task concluída sem implementação

```cypher
MATCH (t:Task)

WHERE t.status = "done"

AND NOT EXISTS {
    MATCH (t)-[:IMPLEMENTED_BY]->(:CodeArtifact)
}

RETURN t.id;
```

## ADR sem consumidores

```cypher
MATCH (a:ADR)

WHERE NOT EXISTS {
    MATCH (:Spec)-[:CONSTRAINED_BY]->(a)
}

RETURN a.id;
```

## Código relacionado a uma feature removida

```cypher
MATCH
  (s:Spec {status: "removed"})
  -[:DECOMPOSED_INTO]->(:Task)
  -[:IMPLEMENTED_BY]->(code:CodeArtifact)

RETURN code.id;
```

---

# 13. CI como Architecture Gate

Essas consultas podem entrar na pipeline.

Exemplo:

```text
Build
  │
  ▼
Unit Tests
  │
  ▼
E2E Tests
  │
  ▼
Graph Sync
  │
  ▼
Architecture Graph Validation
  │
  ▼
Merge allowed
```

Falha:

```text
ARCHITECTURE GRAPH VALIDATION FAILED

2 inconsistencies found:

SPEC-AUTH-004
  → no acceptance test

TASK-RBAC-013
  → status = done
  → no IMPLEMENTED_BY relationship
```

Isso transforma a arquitetura em algo parcialmente verificável.

---

# 14. Integração com Spec Kit

Fluxo tradicional:

```text
/constitution
     ↓
/specify
     ↓
/clarify
     ↓
/plan
     ↓
/tasks
     ↓
/implement
```

Com Graph Engineering:

```text
/constitution
     │
     ▼
/specify
     │
     └──► GRAPH SYNC
     │
     ▼
/clarify
     │
     └──► GRAPH VALIDATE
     │
     ▼
/plan
     │
     └──► IMPACT ANALYSIS
     │
     ▼
/tasks
     │
     ├──► BUILD TASK DAG
     ├──► DETECT CONFLICTS
     └──► CALCULATE PARALLEL WAVES
     │
     ▼
/implement
     │
     ├──► BUILD CONTEXT SUBGRAPH
     │
     ├──► ALLOCATE WORKTREE
     │
     └──► SPAWN AGENT
     │
     ▼
     PR
     │
     ├──► GRAPH DIFF
     │
     ├──► SPEC DRIFT CHECK
     │
     ├──► IMPACT CHECK
     │
     └──► VALIDATION
```

---

# 15. Estrutura sugerida no repositório

```text
repo/
│
├── .specify/
│   ├── constitution.md
│   ├── memory/
│   └── templates/
│
├── specs/
│   ├── auth/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   │
│   └── rbac/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
│
├── docs/
│   └── adr/
│
├── src/
├── tests/
│
└── engineering-graph/
    │
    ├── schema/
    │   ├── nodes.yaml
    │   └── relationships.yaml
    │
    ├── queries/
    │   ├── impact.cypher
    │   ├── ready-tasks.cypher
    │   ├── conflicts.cypher
    │   ├── drift.cypher
    │   └── agent-context.cypher
    │
    ├── sync/
    │   ├── specs.py
    │   ├── code.py
    │   ├── git.py
    │   └── sync.py
    │
    └── docker-compose.yml
```

---

# 16. Componentes principais

## Graph Sync

Responsável por transformar o repositório em grafo.

```text
Specs
ADRs
Tasks
Code
Tests
Git
 │
 ▼
Graph Sync
 │
 ▼
Neo4j
```

Inicialmente ele não precisa interpretar AST.

Pode trabalhar apenas com:

- frontmatter das specs;
- convenções de paths;
- metadados Git;
- referências explícitas entre artefatos.

---

## Context Builder

Recebe uma Task e consulta o subgrafo relevante.

```text
Task
 │
 ▼
Neo4j traversal
 │
 ▼
Relevant subgraph
 │
 ▼
Context Package
 │
 ▼
Agent
```

---

## Graph Validator

Executa invariantes.

Exemplos:

```text
Every active Spec must have at least one Task.

Every completed Task must have implementation.

Every critical Requirement must have validation.

Every changed ADR must trigger impact analysis.
```

---

## Execution Planner

Analisa:

- dependências;
- tasks READY;
- artefatos compartilhados;
- risco de conflito;
- possíveis waves de execução.

Resultado:

```text
Wave 1
├── Agent A → TASK-101
├── Agent B → TASK-102
└── Agent C → TASK-103

Wave 2
└── Agent D → TASK-104
```

---

# 17. Futuro: GraphRAG

Depois da estrutura básica funcionar, podemos combinar relações explícitas com busca semântica.

Exemplo:

```text
User:
"Estamos implementando impersonation.
Quais decisões arquiteturais anteriores são relevantes?"
```

Busca vetorial poderia encontrar:

```text
ADR-012 RBAC
ADR-017 Authentication
ADR-021 Audit
```

O grafo então expande os resultados:

```text
ADR-017
   │
   ▼
SPEC-AUTH
   │
   ▼
token-service
   │
   ▼
audit middleware
```

Assim temos:

```text
Semantic Search
      +
Graph Traversal
      ↓
Better Retrieval
```

Esse modelo tende a ser mais útil do que RAG puramente vetorial para arquitetura de software.

---

# 18. O que NÃO fazer na V1

Evitar começar com:

- análise completa de AST;
- embeddings de todo o repositório;
- GraphRAG complexo;
- scheduler distribuído;
- dezenas de tipos de nós;
- relações inferidas por IA;
- Neo4j como source of truth;
- agentes escrevendo diretamente no banco.

Tudo isso aumenta a complexidade antes de provar o valor do grafo.

---

# 19. V1 recomendada

Começar com:

## 7 tipos de nós

```text
Requirement
Spec
ADR
Task
CodeArtifact
Test
PullRequest
```

## Relacionamentos essenciais

```text
REALIZED_BY
CONSTRAINED_BY
DECOMPOSED_INTO
DEPENDS_ON
IMPLEMENTED_BY
VALIDATED_BY
IMPLEMENTS
CHANGES
```

## Cinco queries fundamentais

```text
impact
ready
conflicts
drift
context
```

Essas cinco consultas já permitem provar praticamente toda a hipótese.

---

# 20. Roadmap sugerido

## V1 — Traceability Graph

Objetivo:

> Tornar explícitas as relações entre specs, tasks, código e testes.

Entregas:

- Neo4j local;
- schema inicial;
- Graph Sync;
- cinco queries fundamentais;
- validação no CI.

---

## V2 — Agent Context Graph

Objetivo:

> Usar o grafo para controlar contexto dos agentes.

Entregas:

- Context Builder;
- criação automática de context packages;
- suporte a Claude Code/Codex;
- relação Task → files → tests → ADRs.

---

## V3 — Execution Graph

Objetivo:

> Controlar paralelização.

Entregas:

- task DAG;
- READY/BLOCKED;
- conflito de artefatos;
- waves de execução;
- alocação de worktrees.

---

## V4 — GraphRAG

Objetivo:

> Combinar arquitetura explícita com busca semântica.

Entregas:

- embeddings;
- vector search;
- semantic ADR discovery;
- graph expansion;
- retrieval híbrido.

---

# 21. Visão final

O objetivo não é simplesmente:

```text
Spec Kit + Neo4j
```

A arquitetura completa seria:

```text
             Specifications
                   │
                   ▼
            Engineering Graph
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
      Agents      CI       Planning
        │          │          │
        └──────────┼──────────┘
                   ▼
              Pull Requests
                   │
                   ▼
             Graph Validation
                   │
                   ▼
                  Git
```

Conceitualmente:

```text
Spec-Driven Development
          +
Graph-Driven Engineering
          +
Agent-Driven Development
          │
          ▼
Engineering Control Plane
```

O grafo passa a ser a camada que conecta:

- intenção;
- arquitetura;
- planejamento;
- implementação;
- testes;
- agentes;
- Pull Requests;
- execução paralela.

O ganho não está simplesmente em “usar Neo4j”.

O ganho é transformar conhecimento arquitetural e dependências antes implícitas em **informação estruturada, consultável e utilizável por humanos, CI e agentes**.
