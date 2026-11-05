# refinar-tecnicamente

Skill de refinamento técnico: fecha as lacunas técnicas de uma spec já produzida pelo
[`gerador-hu`](https://github.com/pedroct/gerador-de-hu), registra a abordagem técnica e estima
Story Points ancorados em itens fechados comparáveis, gravando o resultado em
`Custom.DemandaSpecTecnica` na Demanda de Negócio.

A sessão roda **por perfil** (`fullstack` ou `mobile`): cada perfil fecha só as suas lacunas e
escreve só a sua subseção de `## Abordagem técnica` (`### Escopo Fullstack (API/Web)` /
`### Escopo Mobile`), sem apagar a do outro. O fluxo completo, em 8 passos, está no
[`SKILL.md`](SKILL.md).

## Instalação

```bash
npx skills add pedroct/refinamento-planejamento-tecnico --skill refinar-tecnicamente -a claude-code
```

## Configuração

Copie `.env.example` para `.env` e preencha organização, projeto e token do Azure DevOps. O token
nunca deve ser versionado. Detalhes (escopo do PAT, variáveis de cada skill) no
[README da raiz](../README.md#configuração).

## Como executar

Não há binário instalado globalmente — a CLI roda dentro do próprio ambiente `uv` desta pasta. As
variáveis do `.env` não são lidas automaticamente: exporte-as antes de chamar o comando, e use
caminho absoluto para argumentos de arquivo (o `--directory` muda o diretório de trabalho para
dentro desta pasta).

```bash
uv sync --directory refinar-tecnicamente   # só na primeira vez, ou após atualizar dependências
export $(grep -v '^#' refinar-tecnicamente/.env | xargs)

uv run --directory refinar-tecnicamente refinar-tecnicamente resolver-spec \
  --demanda 13959 --raiz /caminho/absoluto/do/repositorio
uv run --directory refinar-tecnicamente refinar-tecnicamente resolver-spec \
  --demanda 13959 --raiz /caminho/absoluto/do/repositorio --forcar-remoto
uv run --directory refinar-tecnicamente refinar-tecnicamente ler-lacunas \
  /caminho/absoluto/spec.md --perfil fullstack   # ou mobile; sem --perfil devolve todas
uv run --directory refinar-tecnicamente refinar-tecnicamente sugerir-story-points \
  --area-path "Projeto\\Time A" --tipo "User Story" --tipo Bug
uv run --directory refinar-tecnicamente refinar-tecnicamente gravar-spec-tecnica \
  --demanda 13959 --spec /caminho/absoluto/spec.md --backlog /caminho/absoluto/backlog.md
```

`resolver-spec` sozinho devolve a pasta local quando existe; `--forcar-remoto` baixa o anexo mais
recente para `DN-<id>-<slug>.remoto/` (ignorada pelo git), sem tocar na local — é como uma sessão lê
a subseção que o outro perfil publicou. `--backlog` é opcional em `gravar-spec-tecnica`.

Os comandos acima assumem que você está na raiz do repositório `refinamento-planejamento-tecnico`;
rodando já de dentro desta pasta, omita o prefixo `refinar-tecnicamente/` e o `--directory
refinar-tecnicamente`.
