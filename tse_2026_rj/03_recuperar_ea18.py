import csv
import json
import time
from pathlib import Path

import requests


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA = Path(r"D:\Downloads\eleicoes_2026\tse_2026_rj")

ARQUIVO_FALTANTES = PASTA / "faltantes_ea18.csv"

PASTA_EA18 = PASTA / "ea18"

ARQUIVO_FALHAS = PASTA / "faltantes_ea18_apos_retry.csv"

ARQUIVO_RECUPERADOS = PASTA / "recuperados_ea18.csv"

ARQUIVO_NOSUCHKEY = PASTA / "ea18_nosuchkey.csv"


# Quantas vezes tentar cada arquivo
TENTATIVAS = 2

# Intervalo entre arquivos
INTERVALO = 0.5

# Timeout:
# conexão = 30 segundos
# leitura = 90 segundos
TIMEOUT = (30, 90)


# ============================================================
# URL
# ============================================================

BASE_URL = (
    "https://resultados.tse.jus.br/"
    "oficial/ele2026/arquivo-urna/3220/dados/rj"
)


# ============================================================
# SESSÃO
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
})


# ============================================================
# LER CSV
# ============================================================

if not ARQUIVO_FALTANTES.exists():

    print()
    print("ERRO:")
    print("Arquivo não encontrado:")
    print(ARQUIVO_FALTANTES)
    print()

    raise SystemExit(1)


with open(
    ARQUIVO_FALTANTES,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    faltantes = list(csv.DictReader(f))


print()
print("=" * 80)
print("RECUPERAÇÃO DOS EA18 FALTANTES")
print("=" * 80)
print()

print(f"Arquivo: {ARQUIVO_FALTANTES}")
print(f"Total de faltantes: {len(faltantes):,}")
print()


if not faltantes:

    print("NENHUM EA18 FALTANTE.")
    print("Nada para fazer.")

    raise SystemExit(0)


# ============================================================
# PREPARAR PASTA
# ============================================================

PASTA_EA18.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# RESULTADOS
# ============================================================

recuperados = []
falhas = []
nosuchkey = []


# ============================================================
# FUNÇÃO PARA MONTAR URL
# ============================================================

def montar_url(item):

    municipio = str(
        item["municipio_codigo"]
    ).zfill(5)

    zona = str(
        item["zona"]
    ).zfill(4)

    secao = str(
        item["secao"]
    ).zfill(4)

    arquivo = item["arquivo_ea18"]

    url = (
        f"{BASE_URL}/"
        f"{municipio}/"
        f"{zona}/"
        f"{secao}/"
        f"{arquivo}"
    )

    return url


# ============================================================
# PROCESSAMENTO
# ============================================================

total = len(faltantes)


for numero, item in enumerate(faltantes, start=1):

    municipio = str(
        item["municipio_codigo"]
    ).zfill(5)

    municipio_nome = item.get(
        "municipio",
        ""
    )

    zona = str(
        item["zona"]
    ).zfill(4)

    secao = str(
        item["secao"]
    ).zfill(4)

    arquivo = item["arquivo_ea18"]

    destino = PASTA_EA18 / arquivo

    print(
        f"[{numero:,}/{total:,}] "
        f"{municipio_nome} "
        f"Z{zona} "
        f"S{secao}"
    )


    # --------------------------------------------------------
    # Se já existe e não está vazio
    # --------------------------------------------------------

    if destino.exists() and destino.stat().st_size > 0:

        print(
            f"  -> JÁ EXISTE: {arquivo}"
        )

        recuperados.append({
            **item,
            "resultado": "JA_EXISTIA",
        })

        continue


    url = montar_url(item)

    sucesso = False
    ultimo_erro = ""


    # --------------------------------------------------------
    # RETRIES
    # --------------------------------------------------------

    for tentativa in range(1, TENTATIVAS + 1):

        try:

            print(
                f"  -> tentativa "
                f"{tentativa}/{TENTATIVAS}"
            )


            response = session.get(
                url,
                timeout=TIMEOUT
            )


            # =================================================
            # NO SUCH KEY
            # =================================================

            texto = response.text.strip()

            if (
                response.status_code == 404
                and "<Code>NoSuchKey</Code>" in texto
            ):

                ultimo_erro = "NO_SUCH_KEY"

                print(
                    "  -> NO_SUCH_KEY"
                )

                print(
                    "  -> O TSE não encontrou esse arquivo."
                )

                nosuchkey.append({

                    **item,

                    "erro": "NO_SUCH_KEY",

                    "status_http": response.status_code,

                    "url": url,

                })

                # NÃO faz retry
                break


            # =================================================
            # OUTROS ERROS HTTP
            # =================================================

            response.raise_for_status()


            # =================================================
            # VERIFICAR JSON
            # =================================================

            try:

                dados = response.json()

            except requests.exceptions.JSONDecodeError:

                raise ValueError(
                    "Resposta não é JSON"
                )


            # =================================================
            # VERIFICAÇÃO MÍNIMA
            # =================================================

            if not isinstance(dados, dict):

                raise ValueError(
                    "JSON retornado não é um objeto"
                )


            # =================================================
            # SALVAR
            # =================================================

            with open(
                destino,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    dados,
                    f,
                    ensure_ascii=False,
                    separators=(",", ":")
                )


            # =================================================
            # GARANTIR QUE FOI GRAVADO
            # =================================================

            if not destino.exists():

                raise IOError(
                    "Arquivo não foi criado"
                )


            tamanho = destino.stat().st_size


            if tamanho == 0:

                raise IOError(
                    "Arquivo criado está vazio"
                )


            print(
                f"  -> OK "
                f"({tamanho:,} bytes)"
            )


            recuperados.append({

                **item,

                "resultado": "RECUPERADO",

            })


            sucesso = True

            break


        # =====================================================
        # HTTP ERROR
        # =====================================================

        except requests.exceptions.HTTPError as e:

            status = (
                e.response.status_code
                if e.response is not None
                else "?"
            )

            ultimo_erro = (
                f"HTTP {status}: {e}"
            )

            print(
                f"  -> ERRO {ultimo_erro}"
            )


        # =====================================================
        # TIMEOUT
        # =====================================================

        except requests.exceptions.Timeout as e:

            ultimo_erro = (
                f"TIMEOUT: {e}"
            )

            print(
                f"  -> {ultimo_erro}"
            )


        # =====================================================
        # REQUEST ERROR
        # =====================================================

        except requests.exceptions.RequestException as e:

            ultimo_erro = (
                f"REQUEST: {e}"
            )

            print(
                f"  -> ERRO {ultimo_erro}"
            )


        # =====================================================
        # JSON ERROR
        # =====================================================

        except (ValueError, json.JSONDecodeError) as e:

            ultimo_erro = (
                f"JSON: {e}"
            )

            print(
                f"  -> ERRO {ultimo_erro}"
            )


        # =====================================================
        # OUTROS
        # =====================================================

        except Exception as e:

            ultimo_erro = (
                f"{type(e).__name__}: {e}"
            )

            print(
                f"  -> ERRO {ultimo_erro}"
            )


        # =====================================================
        # ESPERA PARA RETRY
        # =====================================================

        if tentativa < TENTATIVAS:

            espera = 2

            print(
                f"  -> aguardando "
                f"{espera}s..."
            )

            time.sleep(espera)


    # ========================================================
    # SE FALHOU
    # ========================================================

    if not sucesso and ultimo_erro != "NO_SUCH_KEY":

        print(
            f"  -> FALHOU APÓS "
            f"{TENTATIVAS} TENTATIVAS"
        )

        falhas.append({

            **item,

            "erro": ultimo_erro,

            "url": url,

        })


    print()

    time.sleep(INTERVALO)


# ============================================================
# FUNÇÃO PARA SALVAR CSV
# ============================================================

def salvar_csv(caminho, registros):

    if not registros:
        return

    campos = list(registros[0].keys())

    with open(
        caminho,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=campos
        )

        writer.writeheader()

        writer.writerows(registros)


# ============================================================
# SALVAR RECUPERADOS
# ============================================================

salvar_csv(
    ARQUIVO_RECUPERADOS,
    recuperados
)


# ============================================================
# SALVAR FALHAS
# ============================================================

if falhas:

    salvar_csv(
        ARQUIVO_FALHAS,
        falhas
    )

else:

    if ARQUIVO_FALHAS.exists():
        ARQUIVO_FALHAS.unlink()


# ============================================================
# SALVAR NO SUCH KEY
# ============================================================

if nosuchkey:

    salvar_csv(
        ARQUIVO_NOSUCHKEY,
        nosuchkey
    )

else:

    if ARQUIVO_NOSUCHKEY.exists():
        ARQUIVO_NOSUCHKEY.unlink()


# ============================================================
# RESUMO
# ============================================================

print()
print("=" * 80)
print("RECUPERAÇÃO FINALIZADA")
print("=" * 80)
print()

print(
    f"Total analisado:          {total:,}"
)

print(
    f"Recuperados/existentes:   {len(recuperados):,}"
)

print(
    f"NoSuchKey:                {len(nosuchkey):,}"
)

print(
    f"Outras falhas:            {len(falhas):,}"
)

print()


if recuperados:

    print("RECUPERADOS:")

    print(
        ARQUIVO_RECUPERADOS
    )

    print()


if nosuchkey:

    print("NO SUCH KEY:")

    print(
        ARQUIVO_NOSUCHKEY
    )

    print()


if falhas:

    print("OUTRAS FALHAS:")

    print(
        ARQUIVO_FALHAS
    )

    print()

else:

    print(
        "Nenhuma falha adicional."
    )

print()