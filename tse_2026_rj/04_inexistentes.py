import csv
import json
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA = Path(r"D:\Downloads\eleicoes_2026\tse_2026_rj")

EA16_FILE = PASTA / "ea16_rj.json"
EA18_CSV = PASTA / "ea18_rj.csv"

PASTA_EA18 = PASTA / "ea18"
PASTA_BU = PASTA / "bu"

SAIDA_EA18 = PASTA / "faltantes_ea18.csv"
SAIDA_BU = PASTA / "faltantes_bu.csv"


# ============================================================
# FUNÇÃO: ESCREVER CSV
# ============================================================

def salvar_csv(caminho, linhas, campos):
    with open(
        caminho,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=campos
        )

        writer.writeheader()
        writer.writerows(linhas)


# ============================================================
# 1. LER EA16
# ============================================================

print("=" * 80)
print("AUDITORIA LOCAL - TSE 2026 RJ")
print("=" * 80)

print()
print("Lendo EA16:")
print(EA16_FILE)

with open(
    EA16_FILE,
    "r",
    encoding="utf-8"
) as f:
    ea16 = json.load(f)


# ============================================================
# 2. MONTAR LISTA DE SEÇÕES ESPERADAS
# ============================================================

secoes_esperadas = []

for abr in ea16.get("abr", []):

    uf = abr.get("cd", "")
    uf_nome = abr.get("ds", "")

    for municipio in abr.get("mu", []):

        municipio_codigo = str(
            municipio.get("cd", "")
        ).zfill(5)

        municipio_nome = municipio.get(
            "nm",
            ""
        )

        for zona in municipio.get("zon", []):

            zona_codigo = str(
                zona.get("cd", "")
            ).zfill(4)

            for secao in zona.get("sec", []):

                secao_codigo = str(
                    secao.get("ns", "")
                ).zfill(4)

                secoes_esperadas.append({
                    "uf": uf,
                    "uf_nome": uf_nome,
                    "municipio_codigo": municipio_codigo,
                    "municipio": municipio_nome,
                    "zona": zona_codigo,
                    "secao": secao_codigo,
                })


# ============================================================
# 3. LISTAR EA18 EXISTENTES
# ============================================================

print()
print("Verificando EA18...")

ea18_existentes = set()

if PASTA_EA18.exists():

    for arquivo in PASTA_EA18.glob("*.json"):

        nome = arquivo.name

        # Exemplo:
        # p003220-rj-m58106-z0149-s0001-aux.json

        partes = nome.replace(
            "-aux.json",
            ""
        ).split("-")

        try:
            municipio = partes[2].replace(
                "m",
                ""
            )

            zona = partes[3].replace(
                "z",
                ""
            )

            secao = partes[4].replace(
                "s",
                ""
            )

            chave = (
                municipio.zfill(5),
                zona.zfill(4),
                secao.zfill(4)
            )

            ea18_existentes.add(chave)

        except Exception:
            pass


# ============================================================
# 4. DESCOBRIR EA18 FALTANTES
# ============================================================

faltantes_ea18 = []

for secao in secoes_esperadas:

    chave = (
        secao["municipio_codigo"],
        secao["zona"],
        secao["secao"]
    )

    if chave not in ea18_existentes:

        faltantes_ea18.append({
            **secao,
            "arquivo_ea18": (
                f"p003220-rj-"
                f"m{secao['municipio_codigo']}-"
                f"z{secao['zona']}-"
                f"s{secao['secao']}-aux.json"
            )
        })


# ============================================================
# 5. LER EA18 CSV
# ============================================================

print()
print("Lendo:")
print(EA18_CSV)

with open(
    EA18_CSV,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    linhas_ea18 = list(reader)


# ============================================================
# 6. DESCOBRIR BUs ESPERADOS
# ============================================================

bus_esperados = []

for linha in linhas_ea18:

    arquivo_bu = (
        linha.get("arquivo_bu")
        or ""
    ).strip()

    if not arquivo_bu:
        continue

    bus_esperados.append({
        "uf": linha.get("uf", ""),
        "municipio_codigo": (
            linha.get(
                "municipio_codigo",
                ""
            ).zfill(5)
        ),
        "municipio": linha.get(
            "municipio",
            ""
        ),
        "zona": (
            linha.get(
                "zona",
                ""
            ).zfill(4)
        ),
        "secao": (
            linha.get(
                "secao",
                ""
            ).zfill(4)
        ),
        "arquivo_bu": arquivo_bu,
    })


# ============================================================
# 7. LISTAR BUs EXISTENTES
# ============================================================

print()
print("Verificando BUs...")

bu_existentes = set()

if PASTA_BU.exists():

    for arquivo in PASTA_BU.iterdir():

        if arquivo.is_file():

            bu_existentes.add(
                arquivo.name
            )


# ============================================================
# 8. DESCOBRIR BUs FALTANTES
# ============================================================

faltantes_bu = []

for bu in bus_esperados:

    if bu["arquivo_bu"] not in bu_existentes:

        faltantes_bu.append(bu)


# ============================================================
# 9. SALVAR RESULTADOS
# ============================================================

salvar_csv(
    SAIDA_EA18,
    faltantes_ea18,
    [
        "uf",
        "uf_nome",
        "municipio_codigo",
        "municipio",
        "zona",
        "secao",
        "arquivo_ea18",
    ]
)

salvar_csv(
    SAIDA_BU,
    faltantes_bu,
    [
        "uf",
        "municipio_codigo",
        "municipio",
        "zona",
        "secao",
        "arquivo_bu",
    ]
)


# ============================================================
# 10. RESUMO
# ============================================================

print()
print("=" * 80)
print("RESULTADO DA AUDITORIA")
print("=" * 80)

print()
print(f"Seções esperadas pelo EA16: {len(secoes_esperadas):,}")
print(f"EA18 encontrados na pasta:  {len(ea18_existentes):,}")
print(f"EA18 faltantes:             {len(faltantes_ea18):,}")

print()
print(f"BUs esperados pelo EA18:    {len(bus_esperados):,}")
print(f"BUs encontrados na pasta:   {len(bu_existentes):,}")
print(f"BUs faltantes:               {len(faltantes_bu):,}")

print()
print("Arquivos gerados:")

print()
print(SAIDA_EA18)

print()
print(SAIDA_BU)

print()
print("=" * 80)


# ============================================================
# 11. MOSTRAR ALGUNS FALTANTES
# ============================================================

if faltantes_ea18:

    print()
    print("PRIMEIROS EA18 FALTANTES:")
    print()

    for item in faltantes_ea18[:20]:

        print(
            f"{item['municipio']} "
            f"Z{item['zona']} "
            f"S{item['secao']}"
        )


if faltantes_bu:

    print()
    print("PRIMEIROS BU FALTANTES:")
    print()

    for item in faltantes_bu[:20]:

        print(
            f"{item['municipio']} "
            f"Z{item['zona']} "
            f"S{item['secao']} "
            f"{item['arquivo_bu']}"
        )


print()
print("Auditoria concluída.")