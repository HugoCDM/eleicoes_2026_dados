# Eleicoes 2026 API

Scripts para baixar, auditar e processar arquivos de urna das eleicoes 2026 no RJ a partir dos dados publicados pelo TSE.

## Acesso Direto aos Dados

Se voce so quer usar a base final ja processada, baixe o arquivo Parquet no Hugging Face:

```text
https://huggingface.co/datasets/HugoCDM/tse_dados_2026_rj/resolve/main/votos_dados_2026_rj.parquet
```

Esse arquivo contem os dados finais de votos ja consolidados. O fluxo abaixo serve para quem quiser reproduzir o processo do zero, baixando os arquivos do TSE passo a passo ate gerar localmente o `csv/votos_2026_rj.csv`.

## Requisitos

- Python 3.10 ou superior
- Acesso a internet para consultar `https://resultados.tse.jus.br`
- Pacotes Python:

```bash
pip install requests pandas asn1tools
```

## Configuracao Importante

Os scripts usam caminhos absolutos no Windows, principalmente:

```text
D:\Downloads\eleicoes_2026\tse_2026_rj
```

Antes de executar, confira a variavel `PASTA` nos scripts e ajuste para o caminho onde voce quer salvar os arquivos baixados e gerados. Se mantiver o caminho original, crie essa pasta antes da execucao.

Estrutura esperada/gerada:

```text
tse_2026_rj/
  ea16_rj.json
  ea18_rj.csv
  secoes_agregadas_nsp.csv
  faltantes_ea18.csv
  faltantes_bu.csv
  ea18/
  bu/
  csv/
    votos_2026_rj.csv
    erros_bu_2026_rj.csv
```

## Gerar os Dados Passo a Passo

Execute os scripts nesta ordem:

```bash
python tse_2026_rj/01_ea16_ea18.py
python tse_2026_rj/03_recuperar_ea18.py
python tse_2026_rj/04_inexistentes.py
python tse_2026_rj/02_bu_votos.py
```

Ao final do processo, o arquivo principal gerado sera:

```text
csv/votos_2026_rj.csv
```

## Scripts

### `01_ea16_ea18.py`

Baixa ou reutiliza o arquivo EA16 do RJ, extrai a lista de secoes, identifica secoes agregadas por `nsp`, baixa os arquivos EA18 e gera CSVs com os metadados encontrados.

Uso:

```bash
python tse_2026_rj/01_ea16_ea18.py
```

Entradas:

- Internet, caso `ea16_rj.json` e/ou arquivos EA18 ainda nao existam localmente.
- `ea16_rj.json`, se ja existir na pasta configurada.

Saidas principais:

- `ea16_rj.json`: configuracao de secoes do TSE.
- `ea18/`: pasta com arquivos EA18 baixados.
- `ea18_rj.csv`: relacao dos EA18 verificados e seus hashes/arquivos associados.
- `secoes_agregadas_nsp.csv`: secoes agregadas e suas secoes principais.
- `faltantes_ea18.csv`: EA18 que falharam durante a consulta.
- `ea18_nosuchkey.csv`: EA18 que o TSE respondeu como `NoSuchKey`.

Observacoes:

- Se um EA18 ja existir localmente e for valido, o script reutiliza o arquivo.
- Para secoes agregadas, o script consulta o EA18 da secao principal indicada por `nsp`.

### `02_bu_votos.py`

Processa os boletins de urna listados em `ea18_rj.csv`, baixa os BUs quando necessario, decodifica os arquivos com ASN.1 e gera um CSV consolidado de votos.

Uso:

```bash
python tse_2026_rj/02_bu_votos.py
```

Entradas:

- `ea18_rj.csv`, gerado pelo `01_ea16_ea18.py`.
- `secoes_agregadas_nsp.csv`, gerado pelo `01_ea16_ea18.py`.
- `bu_v2.asn1`. Se nao existir, o script baixa automaticamente a especificacao ASN.1.
- Internet, caso os BUs ainda nao estejam na pasta `bu/`.

Saidas:

- `bu/`: arquivos BU baixados.
- `csv/votos_2026_rj.csv`: votos consolidados por municipio, zona, secao, cargo, tipo de voto, codigo votavel, partido e quantidade.
- `csv/erros_bu_2026_rj.csv`: BUs que nao foram processados por erro ou ausencia.

Configuracoes uteis no arquivo:

- `LIMITE_SECOES = None`: processa todos os BUs. Para teste, troque por um numero, por exemplo `LIMITE_SECOES = 10`.
- `INTERVALO = 0.05`: pausa entre requisicoes.

### `03_recuperar_ea18.py`

Tenta baixar novamente os EA18 listados em `faltantes_ea18.csv`, usando retry e validacao basica do JSON retornado.

Uso:

```bash
python tse_2026_rj/03_recuperar_ea18.py
```

Entradas:

- `faltantes_ea18.csv`, gerado pelo `01_ea16_ea18.py` ou pelo `04_inexistentes.py`.

Saidas:

- `ea18/`: arquivos EA18 recuperados.
- `recuperados_ea18.csv`: arquivos recuperados ou que ja existiam.
- `faltantes_ea18_apos_retry.csv`: arquivos que continuaram falhando apos as tentativas.
- `ea18_nosuchkey.csv`: arquivos que retornaram `NoSuchKey`.

Configuracoes uteis no arquivo:

- `TENTATIVAS = 2`: quantidade de tentativas para cada arquivo.
- `INTERVALO = 0.5`: pausa entre arquivos.
- `TIMEOUT = (30, 90)`: timeout de conexao e leitura.

### `04_inexistentes.py`

Audita os arquivos locais e compara o que era esperado com o que existe nas pastas `ea18/` e `bu/`.

Uso:

```bash
python tse_2026_rj/04_inexistentes.py
```

Entradas:

- `ea16_rj.json`
- `ea18_rj.csv`
- Pasta `ea18/`
- Pasta `bu/`

Saidas:

- `faltantes_ea18.csv`: secoes esperadas pelo EA16 que nao possuem arquivo EA18 local.
- `faltantes_bu.csv`: BUs esperados pelo `ea18_rj.csv` que nao existem localmente na pasta `bu/`.

Quando usar:

- Depois de baixar EA18 e/ou BUs, para conferir se ficou algo faltando.
- Antes de rodar novamente `03_recuperar_ea18.py`, caso queira atualizar a lista de EA18 ausentes.

## Notebook

### `reader.ipynb`

Notebook auxiliar para exploracao manual dos dados. Use quando quiser abrir, inspecionar ou testar leituras de arquivos gerados pelos scripts. Ele nao substitui o fluxo principal dos scripts numerados.

## Recurso Opcional

### `00_decodificar_bu.py`

Este script nao faz parte do passo a passo para gerar o CSV final. Ele e uma feature auxiliar para quem quiser entender como um boletim de urna (`.dat`) e decodificado com a especificacao ASN.1 `bu_v2.asn1`.

Uso:

```bash
python tse_2026_rj/00_decodificar_bu.py
```

Antes de rodar, ajuste no proprio arquivo:

- O caminho de `bu_v2.asn1`, se necessario.
- O arquivo `.dat` aberto no `with open(...)`.

Entrada esperada:

- `tse_2026_rj/bu_v2.asn1`
- Um arquivo BU `.dat`, por exemplo `tse_2026_rj/bu/o03220rj5800902550024-bu.dat`

Saida:

- Imprime no terminal a estrutura `resultadosVotacaoPorEleicao` decodificada.

## Arquivos Grandes e Gerados

Arquivos de dados como `bu/`, `ea18/`, `csv/`, `.parquet` e CSVs grandes devem ficar fora do Git quando forem apenas resultado de processamento local. Confira o `.gitignore` antes de commitar.
