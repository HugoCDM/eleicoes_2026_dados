import json
import time
from pathlib import Path

import requests
import pandas as pd


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE = "https://resultados.tse.jus.br"
AMBIENTE = "oficial"
CICLO = "ele2026"
UF = "rj"

PLEITO = "3220"
PLEITO_ARQUIVO = PLEITO.zfill(6)


# ============================================================
# PASTAS
# ============================================================

PASTA = Path(r"D:\Downloads\eleicoes_2026\tse_2026_rj")

PASTA_EA18 = PASTA / "ea18"

PASTA.mkdir(
    parents=True,
    exist_ok=True
)

PASTA_EA18.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# ARQUIVOS
# ============================================================

EA16_FILE = PASTA / "ea16_rj.json"
CSV_FILE = PASTA / "ea18_rj.csv"

CSV_AGREGADAS = (
    PASTA / "secoes_agregadas_nsp.csv"
)

CSV_FALTANTES = (
    PASTA / "faltantes_ea18.csv"
)

CSV_NOSUCHKEY = (
    PASTA / "ea18_nosuchkey.csv"
)


# ============================================================
# URL EA16
# ============================================================

EA16_URL = (
    f"{BASE}/"
    f"{AMBIENTE}/"
    f"{CICLO}/"
    f"arquivo-urna/"
    f"{PLEITO}/"
    f"config/"
    f"{UF}/"
    f"{UF}-p{PLEITO_ARQUIVO}-cs.json"
)


# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


# ============================================================
# SALVAR JSON
# ============================================================

def salvar_json(caminho, dados):

    caminho.write_text(
        json.dumps(
            dados,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


# ============================================================
# BAIXAR EA16
# ============================================================

print("=" * 70)
print("CARREGANDO EA16")
print("=" * 70)

if EA16_FILE.exists():

    print(
        f"Usando EA16 existente: {EA16_FILE}"
    )

    ea16 = json.loads(
        EA16_FILE.read_text(
            encoding="utf-8"
        )
    )

else:

    print(
        "EA16 não encontrado localmente."
    )

    print(
        f"Baixando: {EA16_URL}"
    )

    response = session.get(
        EA16_URL,
        timeout=30
    )

    response.raise_for_status()

    ea16 = response.json()

    salvar_json(
        EA16_FILE,
        ea16
    )

    print(
        f"EA16 salvo em: {EA16_FILE}"
    )


# ============================================================
# VALIDAR ESTRUTURA
# ============================================================

print()
print("=" * 70)
print("ESTRUTURA")
print("=" * 70)

print(
    "Chaves:",
    list(ea16.keys())
)

print(
    "Quantidade de UFs:",
    len(ea16.get("abr", []))
)


# ============================================================
# EXTRAIR SEÇÕES
# ============================================================

secoes = []
secoes_proprias = []
secoes_agregadas = []

for abrangencia in ea16.get("abr", []):

    uf = abrangencia.get("cd")
    uf_nome = abrangencia.get("ds")

    for municipio in abrangencia.get("mu", []):

        municipio_codigo = municipio.get("cd")
        municipio_nome = municipio.get("nm")

        for zona in municipio.get("zon", []):

            zona_codigo = zona.get("cd")

            for secao in zona.get("sec", []):

                numero_secao = secao.get("ns")

                nsp = secao.get("nsp")

                data_ea18 = secao.get("da")
                hora_ea18 = secao.get("ha")

                registro = {
                    "uf": uf,
                    "uf_nome": uf_nome,

                    "municipio_codigo": str(
                        municipio_codigo
                    ).zfill(5),

                    "municipio": municipio_nome,

                    "zona": str(
                        zona_codigo
                    ).zfill(4),

                    "secao": str(
                        numero_secao
                    ).zfill(4),

                    "nsp": (
                        str(nsp).zfill(4)
                        if nsp
                        else ""
                    ),

                    "data_ea18": data_ea18,
                    "hora_ea18": hora_ea18,
                }

                secoes.append(registro)

                # ------------------------------------------------
                # SEÇÃO AGREGADA
                # ------------------------------------------------

                if nsp:

                    secoes_agregadas.append(
                        registro
                    )

                # ------------------------------------------------
                # SEÇÃO PRÓPRIA
                # ------------------------------------------------

                else:

                    secoes_proprias.append(
                        registro
                    )


# ============================================================
# RESUMO EA16
# ============================================================

print()
print("=" * 70)
print("RESUMO DO EA16")
print("=" * 70)

print(
    f"Total de seções:          {len(secoes):,}"
)

print(
    f"Seções próprias:           {len(secoes_proprias):,}"
)

print(
    f"Seções agregadas (nsp):    {len(secoes_agregadas):,}"
)


# ============================================================
# SALVAR RELAÇÕES NSP
# ============================================================

if secoes_agregadas:

    df_agregadas = pd.DataFrame(
        secoes_agregadas
    )

    df_agregadas[
        [
            "uf",
            "municipio_codigo",
            "municipio",
            "zona",
            "secao",
            "nsp",
            "data_ea18",
            "hora_ea18",
        ]
    ].to_csv(
        CSV_AGREGADAS,
        index=False,
        encoding="utf-8-sig"
    )

else:

    pd.DataFrame(
        columns=[
            "uf",
            "municipio_codigo",
            "municipio",
            "zona",
            "secao",
            "nsp",
            "data_ea18",
            "hora_ea18",
        ]
    ).to_csv(
        CSV_AGREGADAS,
        index=False,
        encoding="utf-8-sig"
    )


print()
print(
    f"Relações nsp salvas em:"
)

print(
    CSV_AGREGADAS
)


# ============================================================
# FUNÇÃO URL EA18
# ============================================================

def url_ea18(secao):

    return (
        f"{BASE}/"
        f"{AMBIENTE}/"
        f"{CICLO}/"
        f"arquivo-urna/"
        f"{PLEITO}/"
        f"dados/"
        f"{secao['uf']}/"
        f"{secao['municipio_codigo']}/"
        f"{secao['zona']}/"
        f"{secao['secao']}/"
        f"p{PLEITO_ARQUIVO}-"
        f"{secao['uf']}-"
        f"m{secao['municipio_codigo']}-"
        f"z{secao['zona']}-"
        f"s{secao['secao']}"
        f"-aux.json"
    )


# ============================================================
# NOME LOCAL EA18
# ============================================================

def caminho_ea18(secao):

    return (
        PASTA_EA18
        /
        (
            f"p{PLEITO_ARQUIVO}-"
            f"{secao['uf']}-"
            f"m{secao['municipio_codigo']}-"
            f"z{secao['zona']}-"
            f"s{secao['secao']}-"
            f"aux.json"
        )
    )


# ============================================================
# DOWNLOAD / LEITURA EA18
# ============================================================

def obter_ea18(secao):

    arquivo_local = caminho_ea18(
        secao
    )

    url = url_ea18(
        secao
    )

    # --------------------------------------------------------
    # EXISTE LOCALMENTE
    # --------------------------------------------------------

    if arquivo_local.exists():

        try:

            tamanho = arquivo_local.stat().st_size

            if tamanho > 0:

                ea18 = json.loads(
                    arquivo_local.read_text(
                        encoding="utf-8"
                    )
                )

                return (
                    ea18,
                    200,
                    "LOCAL",
                    url
                )

        except Exception:

            print(
                "    -> arquivo local inválido; "
                "será baixado novamente"
            )

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    try:

        response = session.get(
            url,
            timeout=30
        )

        # ----------------------------------------------------
        # NO SUCH KEY
        # ----------------------------------------------------

        if (
            response.status_code == 404
            and "<Code>NoSuchKey</Code>"
            in response.text
        ):

            return (
                None,
                404,
                "NO_SUCH_KEY",
                url
            )

        # ----------------------------------------------------
        # OUTROS 404
        # ----------------------------------------------------

        if response.status_code == 404:

            return (
                None,
                404,
                "404",
                url
            )

        response.raise_for_status()

        ea18 = response.json()

        salvar_json(
            arquivo_local,
            ea18
        )

        return (
            ea18,
            200,
            "DOWNLOAD",
            url
        )

    except requests.RequestException as e:

        return (
            None,
            None,
            f"REQUEST_ERROR: {e}",
            url
        )

    except Exception as e:

        return (
            None,
            None,
            f"JSON_ERROR: {e}",
            url
        )


# ============================================================
# DADOS DE HASH
# ============================================================

def extrair_resultados(secao, ea18, status_http, origem):

    # URL do EA18 desta seção
    url = url_ea18(secao)

    resultados = []

    idg = ea18.get("idg")
    situacao_secao = ea18.get("st")

    hashes = ea18.get(
        "hashes",
        []
    )

    for item_hash in hashes:

        hash_value = item_hash.get(
            "hash"
        )

        arquivos = item_hash.get(
            "arq",
            []
        )

        nomes_arquivos = [
            arquivo.get("nm")
            for arquivo in arquivos
            if arquivo.get("nm")
        ]

        tipos_arquivos = [
            arquivo.get("tp")
            for arquivo in arquivos
            if arquivo.get("tp")
        ]

        arquivo_bu = None

        for arquivo in arquivos:

            if arquivo.get("tp") == "bu":

                arquivo_bu = arquivo.get(
                    "nm"
                )

                break

        url_bu = None

        if hash_value and arquivo_bu:

            url_bu = (
                f"{BASE}/"
                f"{AMBIENTE}/"
                f"{CICLO}/"
                f"arquivo-urna/"
                f"{PLEITO}/"
                f"dados/"
                f"{secao['uf']}/"
                f"{secao['municipio_codigo']}/"
                f"{secao['zona']}/"
                f"{secao['secao']}/"
                f"{hash_value}/"
                f"{arquivo_bu}"
            )

        resultados.append({

            **secao,

            "status_http": status_http,
            "origem_ea18": origem,

            "url_ea18": url,

            "idg": idg,
            "situacao_secao": situacao_secao,

            "hash": hash_value,

            "data_hash": item_hash.get(
                "dr"
            ),

            "hora_hash": item_hash.get(
                "hr"
            ),

            "situacao_hash": item_hash.get(
                "st"
            ),

            "arquivos": " | ".join(
                nomes_arquivos
            ),

            "tipos_arquivos": " | ".join(
                tipos_arquivos
            ),

            "arquivo_bu": arquivo_bu,

            "url_bu": url_bu,
        })

    # --------------------------------------------------------
    # EA18 sem hashes
    # --------------------------------------------------------

    if not hashes:

        resultados.append({

            **secao,

            "status_http": status_http,
            "origem_ea18": origem,

            "url_ea18": url,

            "idg": idg,
            "situacao_secao": situacao_secao,

            "hash": None,
            "data_hash": None,
            "hora_hash": None,
            "situacao_hash": None,

            "arquivos": None,
            "tipos_arquivos": None,

            "arquivo_bu": None,
            "url_bu": None,
        })

    return resultados


# ============================================================
# PROCESSAR UMA SEÇÃO
# ============================================================

def processar_secao(secao):

    ea18, status, origem, url = obter_ea18(
        secao
    )

    if ea18 is None:

        return [{
            **secao,

            "status_http": status,
            "origem_ea18": origem,

            "url_ea18": url,

            "idg": None,
            "situacao_secao": None,

            "hash": None,
            "data_hash": None,
            "hora_hash": None,
            "situacao_hash": None,

            "arquivos": None,
            "tipos_arquivos": None,

            "arquivo_bu": None,
            "url_bu": None,
        }]

    return extrair_resultados(
        secao,
        ea18,
        status,
        origem
    )


# ============================================================
# ATENÇÃO:
#
# PARA SEÇÕES COM NSP:
#
# não baixamos o EA18 da seção original.
#
# Primeiro verificamos o EA18 da seção principal.
# ============================================================

print()
print("=" * 70)
print("VERIFICANDO EA18")
print("=" * 70)


# ============================================================
# MAPA DE SEÇÕES
# ============================================================

mapa_secoes = {}

for secao in secoes:

    chave = (
        secao["municipio_codigo"],
        secao["zona"],
        secao["secao"],
    )

    mapa_secoes[
        chave
    ] = secao


# ============================================================
# SEÇÕES QUE PRECISAM SER CONSULTADAS
#
# 1. todas as próprias
# 2. todas as seções principais apontadas por nsp
#
# Sem duplicar.
# ============================================================

secoes_para_ea18 = {}

for secao in secoes_proprias:

    chave = (
        secao["municipio_codigo"],
        secao["zona"],
        secao["secao"],
    )

    secoes_para_ea18[
        chave
    ] = secao


for secao in secoes_agregadas:

    nsp = secao["nsp"]

    chave_principal = (
        secao["municipio_codigo"],
        secao["zona"],
        nsp,
    )

    principal = mapa_secoes.get(
        chave_principal
    )

    if principal:

        secoes_para_ea18[
            chave_principal
        ] = principal

    else:

        # ----------------------------------------------------
        # Caso raro: nsp não apareceu no EA16
        # ----------------------------------------------------

        principal = {
            "uf": secao["uf"],
            "uf_nome": secao["uf_nome"],

            "municipio_codigo":
                secao["municipio_codigo"],

            "municipio":
                secao["municipio"],

            "zona":
                secao["zona"],

            "secao":
                nsp,

            "nsp": "",

            "data_ea18": None,
            "hora_ea18": None,
        }

        secoes_para_ea18[
            chave_principal
        ] = principal


print(
    f"Seções próprias: "
    f"{len(secoes_proprias):,}"
)

print(
    f"Seções agregadas: "
    f"{len(secoes_agregadas):,}"
)

print(
    f"EA18 distintos a verificar: "
    f"{len(secoes_para_ea18):,}"
)


# ============================================================
# DOWNLOAD / LEITURA
# ============================================================

resultados = []

faltantes = []
nosuchkey = []

lista_ea18 = list(
    secoes_para_ea18.values()
)

total = len(lista_ea18)

for i, secao in enumerate(
    lista_ea18,
    start=1
):

    print(
        f"[{i:,}/{total:,}] "
        f"{secao['municipio']} "
        f"Z{secao['zona']} "
        f"S{secao['secao']}"
    )

    linhas = processar_secao(
        secao
    )

    resultados.extend(
        linhas
    )

    # --------------------------------------------------------
    # identificar falhas
    # --------------------------------------------------------

    for linha in linhas:

        status = linha.get(
            "status_http"
        )

        origem = linha.get(
            "origem_ea18"
        )

        if status != 200:

            if origem == "NO_SUCH_KEY":

                nosuchkey.append(
                    linha
                )

            else:

                faltantes.append(
                    linha
                )

    time.sleep(
        0.05
    )


# ============================================================
# DATAFRAME
# ============================================================

df = pd.DataFrame(
    resultados
)


# ============================================================
# SALVAR EA18 CSV
# ============================================================

df.to_csv(
    CSV_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# SALVAR FALTANTES
# ============================================================

pd.DataFrame(
    faltantes
).to_csv(
    CSV_FALTANTES,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# SALVAR NOSUCHKEY
# ============================================================

pd.DataFrame(
    nosuchkey
).to_csv(
    CSV_NOSUCHKEY,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# RESUMO
# ============================================================

print()
print("=" * 70)
print("FINALIZADO")
print("=" * 70)

print(
    f"Seções no EA16:              "
    f"{len(secoes):,}"
)

print(
    f"Seções próprias:              "
    f"{len(secoes_proprias):,}"
)

print(
    f"Seções agregadas (nsp):       "
    f"{len(secoes_agregadas):,}"
)

print(
    f"EA18 distintos verificados:   "
    f"{len(lista_ea18):,}"
)

if not df.empty:

    print()

    print(
        f"Linhas no ea18_rj.csv:        "
        f"{len(df):,}"
    )

    print(
        f"EA18 HTTP 200:                "
        f"{(df['status_http'] == 200).sum():,}"
    )

    print(
        f"EA18 HTTP 404:                "
        f"{(df['status_http'] == 404).sum():,}"
    )

    print(
        f"Hashes encontrados:           "
        f"{df['hash'].notna().sum():,}"
    )

    print(
        f"BUs encontrados:              "
        f"{df['arquivo_bu'].notna().sum():,}"
    )

print()

print(
    f"Faltantes: "
    f"{len(faltantes):,}"
)

print(
    f"NoSuchKey: "
    f"{len(nosuchkey):,}"
)

print()

print(
    f"EA18 CSV: "
    f"{CSV_FILE}"
)

print(
    f"Agregadas: "
    f"{CSV_AGREGADAS}"
)

print(
    f"Faltantes: "
    f"{CSV_FALTANTES}"
)

print(
    f"NoSuchKey: "
    f"{CSV_NOSUCHKEY}"
)

print(
    f"Pasta EA18: "
    f"{PASTA_EA18}"
)