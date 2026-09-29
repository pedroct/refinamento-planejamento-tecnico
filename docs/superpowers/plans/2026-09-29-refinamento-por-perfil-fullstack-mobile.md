# Refinamento técnico por perfil (Fullstack/Mobile) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `refinar-tecnicamente` passa a permitir rodar a sessão de entrevista técnica filtrada por
perfil (`fullstack` ou `mobile`), classificando cada lacuna pela evidência de repositório que ela cita,
e o template de `## Abordagem técnica` ganha duas subseções de propriedade exclusiva por perfil, para
que a sessão de um perfil nunca apague o trabalho já gravado pelo outro.

**Architecture:** `leitor_lacunas.py` ganha uma função pura de classificação (`perfil_da_lacuna`) e um
parâmetro opcional em `filtrar_tecnicas`; `cli.py` expõe isso via `--perfil` em `ler-lacunas`. A
"mesclagem" entre perfis não é código — é disciplina de workflow documentada em `SKILL.md`
(buscar a versão mais recente de `spec.md` antes de escrever, tocar só na própria subseção).

**Tech Stack:** Python 3.12, `pytest`, `re` (stdlib, sem dependência nova).

**Spec:** `docs/superpowers/specs/2026-09-29-refinamento-por-perfil-fullstack-mobile-design.md`

## Global Constraints

- Conteúdo criado em português brasileiro.
- Cada arquivo de código alterado tem seu teste equivalente atualizado (convenção do projeto).
- Sem `--perfil`, `ler-lacunas` continua com o comportamento de hoje — mudança aditiva, sem regressão.
- A heurística é só inferência local por regex, sem rede, sem cadastro externo de repositórios.
- Nenhuma mudança em `Lacuna`, `ler_lacunas`, `ErroLacunaAmbigua` ou no parsing existente — só adição.

## Review Focus

- **Lacuna sem nenhum caminho entre crases** (pergunta puramente conceitual, como as da própria
  Demanda 14064) — precisa classificar como `"ambos"`, nunca sumir de nenhum dos dois perfis.
- **Lacuna citando caminho mobile e não-mobile ao mesmo tempo** — também `"ambos"`, não pode cair
  arbitrariamente para um dos dois lados.
- **Nome de repositório com "mobile" como substring mas não como repositório mobile de verdade**
  (ex.: um hipotético `diligencia-mobile-legado` que na real seja outra coisa) — fora de escopo tratar
  caso especial: a spec já declara a heurística como substring simples, documentar a limitação no
  docstring em vez de tentar adivinhar.
- **`--perfil` com valor fora de `{fullstack, mobile}`** — precisa ser rejeitado pelo `argparse` antes
  de qualquer leitura de arquivo (mesmo padrão dos outros argumentos já validados na CLI).
- **`evidencia` citando caminho mobile mas `pergunta` citando caminho não-mobile na mesma lacuna** —
  mesmo caso do segundo item acima (mistura entre os dois campos, não só dentro de um campo só);
  precisa resultar em `"ambos"` também.

---

### Task 1: `perfil_da_lacuna` — classificação por evidência citada

**Files:**
- Modify: `refinar-tecnicamente/src/refinar_tecnicamente/leitor_lacunas.py`
- Test: `refinar-tecnicamente/tests/test_leitor_lacunas.py`

**Interfaces:**
- Consumes: `Lacuna` (já existe, `leitor_lacunas.py`) — campos `pergunta: str`, `evidencia: str | None`.
- Produces:
  - `Perfil = Literal["fullstack", "mobile", "ambos"]`
  - `perfil_da_lacuna(lacuna: Lacuna) -> Perfil`

- [ ] **Step 1: Escrever os testes que falham**

Adicione ao final de `tests/test_leitor_lacunas.py`:

```python
from refinar_tecnicamente.leitor_lacunas import perfil_da_lacuna


def _lacuna(pergunta: str, evidencia: str | None = None) -> Lacuna:
    return Lacuna(id="T1", audiencia="Técnico", pergunta=pergunta, evidencia=evidencia)


def test_perfil_da_lacuna_so_caminho_mobile_na_pergunta() -> None:
    lacuna = _lacuna(
        "O app deve exibir o novo campo? Ver `diligencia-mobile/lib/data/models/x.dart:10`."
    )
    assert perfil_da_lacuna(lacuna) == "mobile"


def test_perfil_da_lacuna_so_caminho_nao_mobile_na_pergunta() -> None:
    lacuna = _lacuna(
        "O filtro deve considerar isso? Ver `diligencia-api/src/main/java/Servico.java:20`."
    )
    assert perfil_da_lacuna(lacuna) == "fullstack"


def test_perfil_da_lacuna_caminhos_mistos_na_pergunta() -> None:
    lacuna = _lacuna(
        "Os dois lados precisam mudar? Ver `diligencia-api/Servico.java:20` e "
        "`diligencia-mobile/lib/x.dart:5`."
    )
    assert perfil_da_lacuna(lacuna) == "ambos"


def test_perfil_da_lacuna_sem_nenhum_caminho() -> None:
    lacuna = _lacuna("Qual a granularidade do acesso a órgãos inativos?")
    assert perfil_da_lacuna(lacuna) == "ambos"


def test_perfil_da_lacuna_usa_evidencia_estruturada() -> None:
    lacuna = _lacuna(
        "O prazo persiste como enum?", evidencia="diligencia-mobile/lib/data/x.dart:12"
    )
    assert perfil_da_lacuna(lacuna) == "mobile"


def test_perfil_da_lacuna_mistura_entre_pergunta_e_evidencia() -> None:
    """Um caminho mobile na pergunta e um não-mobile só na evidência (ou vice-versa) também
    conta como mistura — a classificação olha os dois campos juntos, não cada um isolado."""
    lacuna = _lacuna(
        "Isso afeta os dois lados? Ver `diligencia-mobile/lib/x.dart:5`.",
        evidencia="diligencia-api/Servico.java:20",
    )
    assert perfil_da_lacuna(lacuna) == "ambos"


def test_perfil_da_lacuna_repositorio_com_mobile_como_substring() -> None:
    """A heurística é substring simples, documentada como limitação conhecida — um repositório
    hipotético cujo nome contenha 'mobile' sem ser o app mobile de verdade também classificaria
    como mobile. Este teste fixa o comportamento documentado, não uma falha a corrigir aqui."""
    lacuna = _lacuna("Pergunta qualquer. Ver `algo-mobile-legado/arquivo.py:1`.")
    assert perfil_da_lacuna(lacuna) == "mobile"
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_leitor_lacunas.py -k perfil_da_lacuna -v`
Expected: FAIL — `ImportError: cannot import name 'perfil_da_lacuna'`

- [ ] **Step 3: Implementar**

Em `leitor_lacunas.py`, adicione os imports e a função (após a definição de `Lacuna`, antes de
`_corpo_secao_lacunas`):

```python
from typing import Literal

Perfil = Literal["fullstack", "mobile", "ambos"]

_CAMINHO_ENTRE_CRASES = re.compile(r"`([^`]+)`")


def _e_caminho_mobile(caminho: str) -> bool:
    """O primeiro segmento do caminho (antes de '/') é o nome do repositório; 'mobile' como
    substring nele, case-insensitive, é a convenção observada nos repositórios reais
    (`diligencia-mobile`). Limitação conhecida e aceita: um repositório cujo nome contenha
    'mobile' sem ser o app mobile também classificaria como mobile."""
    repositorio = caminho.split("/", 1)[0]
    return "mobile" in repositorio.lower()


def perfil_da_lacuna(lacuna: Lacuna) -> Perfil:
    """Classifica pelos caminhos citados entre crases na pergunta e na evidência, juntos. Sem
    caminho nenhum, ou caminhos dos dois tipos ao mesmo tempo (mesmo campo ou campos
    diferentes), o resultado é 'ambos' — nunca esconde uma pergunta por excesso de precisão da
    heurística."""
    texto = lacuna.pergunta + " " + (lacuna.evidencia or "")
    caminhos = _CAMINHO_ENTRE_CRASES.findall(texto)
    if not caminhos:
        return "ambos"
    classificacoes = {_e_caminho_mobile(caminho) for caminho in caminhos}
    if len(classificacoes) > 1:
        return "ambos"
    return "mobile" if classificacoes.pop() else "fullstack"
```

Adicione `from typing import Literal` junto aos imports do topo do arquivo (ou ajuste o `import` já
existente, se houver) e mantenha `import re` já presente.

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_leitor_lacunas.py -v`
Expected: PASS (todos, incluindo os já existentes — sem regressão)

- [ ] **Step 5: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/leitor_lacunas.py tests/test_leitor_lacunas.py
git commit -m "feat(refinar-tecnicamente): classificar lacuna técnica por perfil (fullstack/mobile)"
```

---

### Task 2: `filtrar_tecnicas` — filtro aditivo por perfil

**Files:**
- Modify: `refinar-tecnicamente/src/refinar_tecnicamente/leitor_lacunas.py`
- Test: `refinar-tecnicamente/tests/test_leitor_lacunas.py`

**Interfaces:**
- Consumes: `perfil_da_lacuna` (Task 1), `Perfil` (Task 1).
- Produces: `filtrar_tecnicas(lacunas: list[Lacuna], perfil: Perfil | None = None) -> list[Lacuna]`
  (assinatura estendida — compatível com todo código que já chama `filtrar_tecnicas(lacunas)` sem o
  novo parâmetro).

- [ ] **Step 1: Escrever os testes que falham**

Adicione ao final de `tests/test_leitor_lacunas.py`:

```python
_SPEC_MISTA = """# Spec

## Lacunas e perguntas abertas

- **N1 · Negócio** — Pergunta de negócio, nunca deve aparecer em nenhum filtro por perfil.
- **T1 · Técnico** — Endpoint novo? Ver `diligencia-api/Servico.java:10`.
- **T2 · Técnico** — Tela nova? Ver `diligencia-mobile/lib/x.dart:5`.
- **T3 · Técnico** — Pergunta conceitual, sem caminho nenhum citado.
"""


def test_filtrar_tecnicas_por_perfil_fullstack() -> None:
    lacunas = ler_lacunas(_SPEC_MISTA)
    tecnicas = filtrar_tecnicas(lacunas, perfil="fullstack")
    assert [lacuna.id for lacuna in tecnicas] == ["T1", "T3"]


def test_filtrar_tecnicas_por_perfil_mobile() -> None:
    lacunas = ler_lacunas(_SPEC_MISTA)
    tecnicas = filtrar_tecnicas(lacunas, perfil="mobile")
    assert [lacuna.id for lacuna in tecnicas] == ["T2", "T3"]


def test_filtrar_tecnicas_sem_perfil_preserva_comportamento_atual() -> None:
    """Regressão: omitir `perfil` (ou passar None) devolve exatamente o que `filtrar_tecnicas`
    já devolvia antes desta task — todas as lacunas Técnico e sem rótulo, sem filtro nenhum por
    repositório."""
    lacunas = ler_lacunas(_SPEC_MISTA)
    assert [lacuna.id for lacuna in filtrar_tecnicas(lacunas)] == ["T1", "T2", "T3"]
    assert [lacuna.id for lacuna in filtrar_tecnicas(lacunas, perfil=None)] == ["T1", "T2", "T3"]
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_leitor_lacunas.py -k filtrar_tecnicas_por_perfil -v`
Expected: FAIL — `TypeError: filtrar_tecnicas() got an unexpected keyword argument 'perfil'`

- [ ] **Step 3: Implementar**

Troque a função `filtrar_tecnicas` existente por:

```python
def filtrar_tecnicas(lacunas: list[Lacuna], perfil: Perfil | None = None) -> list[Lacuna]:
    """Devolve as lacunas Técnico e as sem rótulo, preservando a ordem original. Quando `perfil`
    é informado, descarta também as que `perfil_da_lacuna` classifica para o outro perfil —
    lacunas 'ambos' sempre passam, em qualquer perfil."""
    tecnicas = [lacuna for lacuna in lacunas if lacuna.audiencia in (None, "Técnico")]
    if perfil is None:
        return tecnicas
    return [
        lacuna
        for lacuna in tecnicas
        if perfil_da_lacuna(lacuna) in (perfil, "ambos")
    ]
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_leitor_lacunas.py -v`
Expected: PASS (todos)

- [ ] **Step 5: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/leitor_lacunas.py tests/test_leitor_lacunas.py
git commit -m "feat(refinar-tecnicamente): filtrar lacunas técnicas por perfil em filtrar_tecnicas"
```

---

### Task 3: CLI — `ler-lacunas --perfil {fullstack,mobile}`

**Files:**
- Modify: `refinar-tecnicamente/src/refinar_tecnicamente/cli.py`
- Test: `refinar-tecnicamente/tests/test_cli.py`

**Interfaces:**
- Consumes: `filtrar_tecnicas(lacunas, perfil=...)` (Task 2).
- Produces: nenhuma interface nova — só expõe `--perfil` no subcomando `ler-lacunas` já existente.

- [ ] **Step 1: Escrever os testes que falham**

Adicione a `tests/test_cli.py`, próximo aos testes de `ler-lacunas` já existentes:

```python
_SPEC_MISTA_PERFIL = """# Spec

## Lacunas e perguntas abertas

- **T1 · Técnico** — Endpoint novo? Ver `diligencia-api/Servico.java:10`.
- **T2 · Técnico** — Tela nova? Ver `diligencia-mobile/lib/x.dart:5`.
"""


def test_ler_lacunas_com_perfil_mobile_filtra_saida(tmp_path: Path, capsys: object) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text(_SPEC_MISTA_PERFIL, encoding="utf-8")
    codigo = executar(["ler-lacunas", str(spec), "--perfil", "mobile"], env=_ENV)
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    lacunas = json.loads(saida)
    assert codigo == 0
    assert [lacuna["id"] for lacuna in lacunas] == ["T2"]


def test_ler_lacunas_com_perfil_fullstack_filtra_saida(tmp_path: Path, capsys: object) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text(_SPEC_MISTA_PERFIL, encoding="utf-8")
    codigo = executar(["ler-lacunas", str(spec), "--perfil", "fullstack"], env=_ENV)
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    lacunas = json.loads(saida)
    assert codigo == 0
    assert [lacuna["id"] for lacuna in lacunas] == ["T1"]


def test_ler_lacunas_com_perfil_invalido_devolve_erro_de_uso(
    tmp_path: Path, capsys: object
) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text(_SPEC_MISTA_PERFIL, encoding="utf-8")
    codigo = executar(["ler-lacunas", str(spec), "--perfil", "backend"], env=_ENV)
    assert codigo == 2


def test_ler_lacunas_sem_perfil_continua_sem_filtro(tmp_path: Path, capsys: object) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text(_SPEC_MISTA_PERFIL, encoding="utf-8")
    codigo = executar(["ler-lacunas", str(spec)], env=_ENV)
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    lacunas = json.loads(saida)
    assert codigo == 0
    assert [lacuna["id"] for lacuna in lacunas] == ["T1", "T2"]
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cli.py -k "ler_lacunas_com_perfil or ler_lacunas_sem_perfil" -v`
Expected: FAIL — `SystemExit` inesperado (argparse não reconhece `--perfil`) nos dois primeiros, e o
terceiro passa por acidente (mas roda antes de `--perfil` existir); rode de novo depois do Step 3 para
confirmar os quatro.

- [ ] **Step 3: Implementar**

Em `cli.py`, altere a definição do subparser `ler-lacunas`:

```python
    ler = subs.add_parser("ler-lacunas")
    ler.add_argument("spec")
    ler.add_argument("--perfil", choices=["fullstack", "mobile"], default=None)
```

Altere a chamada e a função `_ler_lacunas`:

```python
        if args.comando == "ler-lacunas":
            return _ler_lacunas(args.spec, args.perfil)
```

```python
def _ler_lacunas(caminho_spec: str, perfil: str | None = None) -> int:
    caminho = Path(caminho_spec)
    if not caminho.is_file():
        print(f"Spec não encontrada: {caminho_spec}")
        return 1
    lacunas = filtrar_tecnicas(ler_lacunas(caminho.read_text(encoding="utf-8")), perfil=perfil)
```

(A linha seguinte, que já monta o `json.dumps(...)` a partir de `lacunas`, permanece igual — só a
origem de `lacunas` muda.)

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cli.py -v`
Expected: PASS (todos, incluindo os já existentes de `ler-lacunas` sem `--perfil`)

- [ ] **Step 5: Rodar a suíte completa da skill**

Run: `cd refinar-tecnicamente && uv run pytest tests -v`
Expected: PASS (todos)

- [ ] **Step 6: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/cli.py tests/test_cli.py
git commit -m "feat(refinar-tecnicamente): expor --perfil em ler-lacunas"
```

---

### Task 4: `SKILL.md` — pergunta de perfil, template de duas subseções, disciplina de mesclagem

**Files:**
- Modify: `refinar-tecnicamente/SKILL.md` (seção "Fluxo obrigatório", passos 1-3)

**Interfaces:**
- Consumes: `ler-lacunas --perfil` (Task 3).
- Produces: instrução atualizada para o agente que conduz o refinamento.

- [ ] **Step 1: Reescrever os passos 1-3 do "Fluxo obrigatório"**

Troque:

```markdown
1. Receba o ID da Demanda no Azure Boards. Rode `resolver-spec --demanda <id> --raiz <raiz do
   repositório atualmente aberto>`: ele procura `docs/specs/DN-<id>-*/` sob essa raiz e, se não
   encontrar, baixa `spec.md`/`backlog.md` do anexo mais recente da própria Demanda e materializa
   uma pasta local a partir deles. Use o caminho impresso em `stdout` nos passos seguintes. Se a
   CLI recusar (nem pasta local, nem anexo), pare e informe que a Demanda ainda não tem spec
   publicada — não peça o caminho manualmente, nem sugira rodar `gerador-hu` você mesmo.
2. Rode `ler-lacunas spec.md` para isolar as lacunas técnicas (e as sem rótulo, que entram em toda
   rodada). Conduza a entrevista em rodadas, no mesmo mecanismo de fronteira do
   `entrevistar-lacunas-requisito`: pergunte os itens que não dependem de resposta ainda em aberto,
   aceite adiamento explícito, nunca feche uma lacuna por inferência silenciosa.
3. Com as lacunas técnicas fechadas, investigue o código-fonte e escreva a seção
   `## Abordagem técnica` em `spec.md`: camadas tocadas, migração quando houver, estratégia de teste.
   Cite `caminho:linha` para cada afirmação, na mesma disciplina do resto da spec.
```

Por:

```markdown
1. Receba o ID da Demanda no Azure Boards. Rode `resolver-spec --demanda <id> --raiz <raiz do
   repositório atualmente aberto>`: ele procura `docs/specs/DN-<id>-*/` sob essa raiz e, se não
   encontrar, baixa `spec.md`/`backlog.md` do anexo mais recente da própria Demanda e materializa
   uma pasta local a partir deles. Use o caminho impresso em `stdout` nos passos seguintes. Se a
   CLI recusar (nem pasta local, nem anexo), pare e informe que a Demanda ainda não tem spec
   publicada — não peça o caminho manualmente, nem sugira rodar `gerador-hu` você mesmo.

   Pergunte, antes de tudo, **qual o perfil de quem está conduzindo esta sessão**: `fullstack`
   (backend + frontend web) ou `mobile`. Cada Demanda pode passar por duas sessões separadas,
   uma por perfil, conduzidas por profissionais diferentes — a resposta desta pergunta decide o
   filtro do passo 2 e a subseção do passo 3.

2. Rode `ler-lacunas spec.md --perfil <fullstack|mobile>` para isolar as lacunas técnicas do
   próprio perfil (e as sem rótulo, que entram em toda rodada; lacunas que citam evidência dos
   dois perfis ao mesmo tempo também entram, por segurança). Conduza a entrevista em rodadas, no
   mesmo mecanismo de fronteira do `entrevistar-lacunas-requisito`: pergunte os itens que não
   dependem de resposta ainda em aberto, aceite adiamento explícito, nunca feche uma lacuna por
   inferência silenciosa.
3. Com as lacunas técnicas do próprio perfil fechadas, investigue o código-fonte e escreva **só a
   subseção do próprio perfil** dentro de `## Abordagem técnica` em `spec.md`:

   ```markdown
   ## Abordagem técnica

   ### Escopo Fullstack (API/Web)
   <camadas tocadas, migração quando houver, estratégia de teste — só repositórios não-mobile>

   ### Escopo Mobile
   <camadas tocadas, migração quando houver, estratégia de teste — só repositórios mobile>
   ```

   Antes de escrever, rode `resolver-spec` de novo para buscar a versão mais recente de
   `spec.md` — ela pode ter sido atualizada pela sessão do outro perfil, publicada em paralelo.
   Monte o `spec.md` final substituindo **só** a subseção do próprio perfil; se a subseção do
   outro perfil já existir no arquivo buscado, ela entra intacta, sem alteração nenhuma. Cite
   `caminho:linha` para cada afirmação, na mesma disciplina do resto da spec.
```

- [ ] **Step 2: Conferir a mudança**

Run: `grep -n "qual o perfil\|Escopo Fullstack\|Escopo Mobile\|--perfil" refinar-tecnicamente/SKILL.md`
Expected: mostra as três ocorrências novas dentro do "Fluxo obrigatório"

- [ ] **Step 3: Commit**

```bash
cd refinar-tecnicamente
git add SKILL.md
git commit -m "docs(refinar-tecnicamente): sessão de refinamento técnico por perfil fullstack/mobile"
```

---

### Task 5: Cobertura de integração do `SKILL.md` (se a skill já tiver suíte de integração)

**Files:**
- Modify: `refinar-tecnicamente/tests/test_skill_integration.py` (criar o arquivo só se ainda não
  existir nenhuma suíte equivalente na skill — confira antes com
  `ls refinar-tecnicamente/tests/test_skill_integration.py`)

**Interfaces:**
- Consumes: texto de `refinar-tecnicamente/SKILL.md` (Task 4).
- Produces: nenhuma interface nova — só fecha a cobertura de texto do `SKILL.md`, no mesmo padrão
  já usado por `entrevistar-lacunas-requisito/tests/test_skill_integration.py`.

- [ ] **Step 1: Verificar se já existe suíte de integração do SKILL.md nesta skill**

Run: `ls refinar-tecnicamente/tests/test_skill_integration.py`

Se o arquivo **não existir**, esta task só adiciona três asserções pontuais dentro de
`refinar-tecnicamente/tests/test_cli.py` (não crie suíte nova do zero para isso: seria
desproporcional ao restante da mudança). Se **existir**, siga os steps abaixo apontando para esse
arquivo em vez de `test_cli.py`.

- [ ] **Step 2: Escrever os testes que falham**

```python
_SKILL_MD = Path(__file__).resolve().parents[1] / "SKILL.md"


def test_skill_md_pergunta_perfil_antes_de_ler_lacunas() -> None:
    texto = _SKILL_MD.read_text(encoding="utf-8")
    assert "qual o perfil de quem está conduzindo esta sessão" in texto
    assert "--perfil <fullstack|mobile>" in texto


def test_skill_md_documenta_as_duas_subsecoes_da_abordagem_tecnica() -> None:
    texto = _SKILL_MD.read_text(encoding="utf-8")
    assert "### Escopo Fullstack (API/Web)" in texto
    assert "### Escopo Mobile" in texto


def test_skill_md_documenta_buscar_versao_mais_recente_antes_de_escrever() -> None:
    texto = _SKILL_MD.read_text(encoding="utf-8")
    assert "substituindo **só** a subseção do próprio perfil" in texto
```

`Path(__file__).resolve().parents[1]` a partir de `tests/test_cli.py` resolve para a raiz de
`refinar-tecnicamente/` — onde `SKILL.md` já vive, ao lado de `tests/` e `src/`.

- [ ] **Step 3: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests -k skill_md -v`
Expected: FAIL antes da Task 4 rodar; se a Task 4 já rodou, PASS de primeira — nesse caso, confirme
lendo o `SKILL.md` para garantir que as três frases realmente batem literalmente, e siga.

- [ ] **Step 4: Rodar a suíte completa da skill**

Run: `cd refinar-tecnicamente && uv run pytest tests -v`
Expected: PASS (todos)

- [ ] **Step 5: Commit**

```bash
cd refinar-tecnicamente
git add tests/
git commit -m "test(refinar-tecnicamente): cobrir texto do SKILL.md sobre sessão por perfil"
```
