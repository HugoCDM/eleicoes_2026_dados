import csv
import json
import sys
import time
from pathlib import Path

import requests


# ============================================================
# DEPENDÊNCIA ASN.1
# ============================================================

try:

    import asn1tools

except ImportError:

    print()
    print("=" * 80)
    print("ERRO: asn1tools não está instalado.")
    print("=" * 80)
    print()

    print("Execute:")

    print()

    print(
        r"C:\Users\hugop\AppData\Local\Programs\Python\Python314\python.exe "
        r"-m pip install asn1tools"
    )

    print()

    sys.exit(1)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE = "https://resultados.tse.jus.br"

AMBIENTE = "oficial"
CICLO = "ele2026"
PLEITO = "3220"


# ============================================================
# PASTAS
# ============================================================

PASTA = Path(
    r"D:\Downloads\eleicoes_2026\tse_2026_rj"
)

PASTA_EA18 = PASTA / "ea18"
PASTA_BU = PASTA / "bu"
PASTA_CSV = PASTA / "csv"


PASTA_BU.mkdir(
    parents=True,
    exist_ok=True
)

PASTA_CSV.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# ARQUIVOS
# ============================================================

CSV_EA18 = (
    PASTA / "ea18_rj.csv"
)

CSV_AGREGADAS = (
    PASTA / "secoes_agregadas_nsp.csv"
)


CSV_VOTOS = (
    PASTA_CSV
    / "votos_2026_rj.csv"
)


CSV_ERROS = (
    PASTA_CSV
    / "erros_bu_2026_rj.csv"
)


# ============================================================
# ASN.1
# ============================================================

SPEC_URL = (
    "https://raw.githubusercontent.com/"
    "alissonlinneker/dataUrnas-br/main/"
    "spec/v2/bu.asn1"
)

SPEC_FILE = (
    PASTA
    / "bu_v2.asn1"
)


# ============================================================
# TESTE
#
# None = todos
# ============================================================

LIMITE_SECOES = None


# ============================================================
# INTERVALO
# ============================================================

INTERVALO = 0.05


# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


# ============================================================
# BAIXAR SPEC
# ============================================================

def baixar_spec():

    if SPEC_FILE.exists():

        print(
            f"Especificação encontrada: "
            f"{SPEC_FILE}"
        )

        return

    print(
        "Baixando especificação ASN.1 V2..."
    )

    response = session.get(
        SPEC_URL,
        timeout=30
    )

    response.raise_for_status()

    SPEC_FILE.write_bytes(
        response.content
    )

    print(
        f"Especificação salva em: "
        f"{SPEC_FILE}"
    )


# ============================================================
# COMPILAR ASN.1
# ============================================================

def compilar_asn1():

    print()
    print(
        "Compilando especificação ASN.1..."
    )

    compiler = asn1tools.compile_files(
        [
            str(SPEC_FILE)
        ],
        codec="ber"
    )

    print(
        "ASN.1 compilado."
    )

    return compiler


# ============================================================
# DECODIFICAR BU
# ============================================================

def decodificar_bu(
    compiler,
    dados
):

    envelope = compiler.decode(
        "EntidadeEnvelopeGenerico",
        bytearray(dados)
    )

    conteudo = envelope.get(
        "conteudo"
    )

    if conteudo is None:

        raise ValueError(
            "Envelope não possui campo 'conteudo'."
        )

    bu = compiler.decode(
        "EntidadeBoletimUrna",
        bytearray(conteudo)
    )

    return envelope, bu


# ============================================================
# CHOICE
# ============================================================

def choice_name(value):

    if isinstance(value, tuple):

        if (
            len(value) == 2
            and isinstance(value[0], str)
        ):

            return value[0]

    return None


def choice_value(value):

    if isinstance(value, tuple):

        if len(value) == 2:

            return value[1]

    return value


# ============================================================
# CARGOS
# ============================================================

CARGOS = {

    "presidente": (
        1,
        "Presidente"
    ),

    "vicePresidente": (
        2,
        "Vice-Presidente"
    ),

    "governador": (
        3,
        "Governador"
    ),

    "viceGovernador": (
        4,
        "Vice-Governador"
    ),

    "senador": (
        5,
        "Senador"
    ),

    "deputadoFederal": (
        6,
        "Deputado Federal"
    ),

    "deputadoEstadual": (
        7,
        "Deputado Estadual"
    ),

    "deputadoDistrital": (
        8,
        "Deputado Distrital"
    ),

    "primeiroSuplenteSenador": (
        9,
        "Primeiro Suplente de Senador"
    ),

    "segundoSuplenteSenador": (
        10,
        "Segundo Suplente de Senador"
    ),

    "prefeito": (
        11,
        "Prefeito"
    ),

    "vicePrefeito": (
        12,
        "Vice-Prefeito"
    ),

    "vereador": (
        13,
        "Vereador"
    ),
}


# ============================================================
# INTERPRETAR CARGO
# ============================================================

def interpretar_cargo(value):

    nome_choice = choice_name(
        value
    )

    valor_choice = choice_value(
        value
    )

    if nome_choice == "cargoConstitucional":

        if isinstance(
            valor_choice,
            str
        ):

            if valor_choice in CARGOS:

                return CARGOS[
                    valor_choice
                ]

            return (
                0,
                valor_choice
            )

        try:

            codigo = int(
                valor_choice
            )

        except Exception:

            return (
                0,
                str(valor_choice)
            )

        mapa_numerico = {

            1: "Presidente",
            2: "Vice-Presidente",
            3: "Governador",
            4: "Vice-Governador",
            5: "Senador",
            6: "Deputado Federal",
            7: "Deputado Estadual",
            8: "Deputado Distrital",
            9: "Primeiro Suplente de Senador",
            10: "Segundo Suplente de Senador",
            11: "Prefeito",
            12: "Vice-Prefeito",
            13: "Vereador",
        }

        return (
            codigo,
            mapa_numerico.get(
                codigo,
                f"Cargo {codigo}"
            )
        )

    if nome_choice == "numeroCargoConsultaLivre":

        try:

            codigo = int(
                valor_choice
            )

        except Exception:

            codigo = 0

        return (
            codigo,
            f"Cargo/Consulta {codigo}"
        )

    if isinstance(
        valor_choice,
        str
    ):

        if valor_choice in CARGOS:

            return CARGOS[
                valor_choice
            ]

    try:

        codigo = int(
            valor_choice
        )

    except Exception:

        return (
            0,
            str(valor_choice)
        )

    return (
        codigo,
        f"Cargo {codigo}"
    )


# ============================================================
# TIPO DE VOTO
# ============================================================

def interpretar_tipo_voto(value):

    nome = choice_name(
        value
    )

    if nome:

        return nome

    value = choice_value(
        value
    )

    mapa = {

        1: "nominal",
        2: "branco",
        3: "nulo",
        4: "legenda",
        5: "cargoSemCandidato",
    }

    return mapa.get(
        value,
        str(value)
    )


# ============================================================
# BYTES → HEX
# ============================================================

def bytes_hex(value):

    if value is None:

        return ""

    if isinstance(
        value,
        bytes
    ):

        return value.hex().upper()

    if isinstance(
        value,
        bytearray
    ):

        return bytes(
            value
        ).hex().upper()

    return str(
        value
    )


# ============================================================
# CARREGAR EA18
# ============================================================

def carregar_ea18():

    if not CSV_EA18.exists():

        print()
        print(
            "ERRO: ea18_rj.csv não encontrado:"
        )

        print(
            CSV_EA18
        )

        sys.exit(1)

    print()
    print(
        "Lendo:",
        CSV_EA18
    )

    with open(
        CSV_EA18,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        leitor = csv.DictReader(
            f
        )

        return list(
            leitor
        )


# ============================================================
# CARREGAR NSP
# ============================================================

def carregar_agregadas():

    mapa = {}

    if not CSV_AGREGADAS.exists():

        print()
        print(
            "Aviso: "
            "secoes_agregadas_nsp.csv não encontrado."
        )

        return mapa

    with open(
        CSV_AGREGADAS,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        leitor = csv.DictReader(
            f
        )

        for linha in leitor:

            chave = (

                linha.get(
                    "municipio_codigo",
                    ""
                ),

                linha.get(
                    "zona",
                    ""
                ),

                linha.get(
                    "secao",
                    ""
                ),
            )

            mapa[chave] = linha

    return mapa


# ============================================================
# PREPARAR BUs
# ============================================================

def preparar_bu(
    linhas,
    mapa_agregadas
):

    resultado = []

    for linha in linhas:

        arquivo_bu = (
            linha.get(
                "arquivo_bu"
            )
            or ""
        ).strip()

        hash_value = (
            linha.get(
                "hash"
            )
            or ""
        ).strip()

        if not arquivo_bu:
            continue

        if not hash_value:
            continue

        municipio = (
            linha.get(
                "municipio_codigo",
                ""
            )
        )

        zona = (
            linha.get(
                "zona",
                ""
            )
        )

        secao = (
            linha.get(
                "secao",
                ""
            )
        )

        chave = (
            municipio,
            zona,
            secao
        )

        # ----------------------------------------------------
        # Verificar se esta é uma seção principal apontada
        # por uma ou mais seções agregadas
        # ----------------------------------------------------

        agregadas = []

        for (
            chave_agregada,
            agregado
        ) in mapa_agregadas.items():

            if (
                chave_agregada[0]
                == municipio
                and chave_agregada[1]
                == zona
                and agregado.get("nsp")
                == secao
            ):

                agregadas.append(
                    agregado.get(
                        "secao"
                    )
                )

        nova = dict(
            linha
        )

        nova[
            "tipo_secao"
        ] = (
            "principal_com_agregadas"
            if agregadas
            else "propria"
        )

        nova[
            "secao_bu"
        ] = secao

        nova[
            "secoes_agregadas"
        ] = "|".join(
            sorted(
                set(
                    agregadas
                )
            )
        )

        resultado.append(
            nova
        )

    # --------------------------------------------------------
    # Remover duplicatas
    #
    # Cada BU físico deve ser processado uma única vez.
    # --------------------------------------------------------

    unicos = {}

    for linha in resultado:

        chave = (

            linha.get(
                "municipio_codigo",
                ""
            ),

            linha.get(
                "zona",
                ""
            ),

            linha.get(
                "secao_bu",
                ""
            ),

            linha.get(
                "hash",
                ""
            ),

        )

        unicos[
            chave
        ] = linha

    return list(
        unicos.values()
    )


# ============================================================
# URL BU
# ============================================================

def url_bu(linha):

    return (

        f"{BASE}/"
        f"{AMBIENTE}/"
        f"{CICLO}/"
        f"arquivo-urna/"
        f"{PLEITO}/"
        f"dados/"
        f"{linha['uf']}/"
        f"{linha['municipio_codigo']}/"
        f"{linha['zona']}/"
        f"{linha['secao_bu']}/"
        f"{linha['hash']}/"
        f"{linha['arquivo_bu']}"

    )


# ============================================================
# BAIXAR BU
# ============================================================

def baixar_bu(linha):

    arquivo_bu = linha[
        "arquivo_bu"
    ]

    caminho = (
        PASTA_BU
        / arquivo_bu
    )

    if caminho.exists():

        tamanho = (
            caminho.stat().st_size
        )

        if tamanho > 0:

            print(
                f"    -> BU já existe "
                f"({tamanho:,} bytes)"
            )

            return caminho

    url = url_bu(
        linha
    )

    print(
        "    -> baixando BU"
    )

    print(
        f"       {url}"
    )

    response = session.get(
        url,
        timeout=60
    )

    if response.status_code == 404:

        raise FileNotFoundError(
            f"BU 404: {url}"
        )

    response.raise_for_status()

    if not response.content:

        raise ValueError(
            "BU retornou conteúdo vazio."
        )

    caminho.write_bytes(
        response.content
    )

    print(
        f"    -> salvo: "
        f"{caminho.name} "
        f"({len(response.content):,} bytes)"
    )

    return caminho


# ============================================================
# EXTRAIR VOTOS
# ============================================================

def extrair_votos(
    bu,
    linha
):

    municipio = (
        linha.get(
            "municipio_codigo"
        )
        or ""
    )

    municipio_nome = (
        linha.get(
            "municipio"
        )
        or ""
    )

    zona = (
        linha.get(
            "zona"
        )
        or ""
    )

    secao_original = (
        linha.get(
            "secao"
        )
        or ""
    )

    secao_bu = (
        linha.get(
            "secao_bu"
        )
        or secao_original
    )

    uf = (
        linha.get(
            "uf"
        )
        or "rj"
    )

    nsp = (
        linha.get(
            "nsp"
        )
        or ""
    )

    tipo_secao = (
        linha.get(
            "tipo_secao"
        )
        or "propria"
    )

    secoes_agregadas = (
        linha.get(
            "secoes_agregadas"
        )
        or ""
    )


    # ========================================================
    # IDENTIFICAÇÃO
    # ========================================================

    identificacao = (

        bu.get(
            "identificacaoSecao"
        )

        or bu.get(
            "identificacao"
        )

        or {}

    )

    if isinstance(
        identificacao,
        tuple
    ):

        identificacao = (
            identificacao[1]
        )


    municipio_zona = (
        identificacao.get(
            "municipioZona",
            {}
        )
    )

    if isinstance(
        municipio_zona,
        tuple
    ):

        municipio_zona = (
            municipio_zona[1]
        )


    municipio_bu = (
        municipio_zona.get(
            "municipio",
            municipio
        )
    )

    zona_bu = (
        municipio_zona.get(
            "zona",
            zona
        )
    )

    secao_bu_real = (
        identificacao.get(
            "secao",
            secao_bu
        )
    )


    # ========================================================
    # LOCAL DE VOTAÇÃO
    # ========================================================

    local_votacao = (
        identificacao.get(
            "localVotacao"
        )
    )

    if local_votacao is None:

        local_votacao = (
            identificacao.get(
                "local"
            )
        )


    # ========================================================
    # DADOS BU
    # ========================================================

    data_emissao = (
        bu.get(
            "dataHoraEmissao"
        )
    )

    fase = (
        bu.get(
            "fase"
        )
    )

    if isinstance(
        fase,
        tuple
    ):

        fase = fase[1]


    resultados_eleicoes = (
        bu.get(
            "resultadosVotacaoPorEleicao",
            []
        )
    )


    linhas = []


    # ========================================================
    # ELEIÇÕES
    # ========================================================

    for resultado_eleicao in (
        resultados_eleicoes
    ):

        id_eleicao = (
            resultado_eleicao.get(
                "idEleicao",
                0
            )
        )

        eleitores_aptos = (
            resultado_eleicao.get(
                "qtdEleitoresAptos",
                0
            )
        )

        eleitores_aptos_secao = (
            resultado_eleicao.get(
                "qtdEleitoresAptosSecao"
            )
        )

        eleitores_aptos_tte = (
            resultado_eleicao.get(
                "qtdEleitoresAptosTTE"
            )
        )

        ultimo_hash = bytes_hex(
            resultado_eleicao.get(
                "ultimoHashVotosVotavel"
            )
        )

        resultados_votacao = (
            resultado_eleicao.get(
                "resultadosVotacao",
                []
            )
        )


        # ====================================================
        # RESULTADOS
        # ====================================================

        for resultado in (
            resultados_votacao
        ):

            comparecimento = (
                resultado.get(
                    "qtdComparecimento",
                    0
                )
            )

            totais_cargos = (
                resultado.get(
                    "totaisVotosCargo",
                    []
                )
            )


            # =================================================
            # CARGOS
            # =================================================

            for total_cargo in (
                totais_cargos
            ):

                codigo_cargo, nome_cargo = (
                    interpretar_cargo(
                        total_cargo.get(
                            "codigoCargo"
                        )
                    )
                )

                ordem_impressao = (
                    total_cargo.get(
                        "ordemImpressao"
                    )
                )

                votos_votaveis = (
                    total_cargo.get(
                        "votosVotaveis",
                        []
                    )
                )


                # =================================================
                # VOTOS
                # =================================================

                for voto in (
                    votos_votaveis
                ):

                    tipo_voto = (
                        interpretar_tipo_voto(
                            voto.get(
                                "tipoVoto"
                            )
                        )
                    )

                    quantidade = (
                        voto.get(
                            "quantidadeVotos",
                            0
                        )
                    )

                    identificacao_votavel = (
                        voto.get(
                            "identificacaoVotavel",
                            {}
                        )
                    )

                    if isinstance(
                        identificacao_votavel,
                        tuple
                    ):

                        identificacao_votavel = (
                            identificacao_votavel[1]
                        )

                    partido = ""
                    codigo_votavel = ""

                    if isinstance(
                        identificacao_votavel,
                        dict
                    ):

                        partido = (
                            identificacao_votavel.get(
                                "partido",
                                ""
                            )
                        )

                        codigo_votavel = (
                            identificacao_votavel.get(
                                "codigo",
                                ""
                            )
                        )

                    ordem_hash = (
                        voto.get(
                            "ordemGeracaoHash"
                        )
                    )

                    hash_voto = bytes_hex(
                        voto.get(
                            "hash"
                        )
                    )


                    linhas.append({

                        # ------------------------------------
                        # ORIGEM
                        # ------------------------------------

                        "uf": uf,

                        "municipio_codigo": str(
                            municipio_bu
                        ).zfill(5),

                        "municipio": (
                            municipio_nome
                        ),

                        "zona": str(
                            zona_bu
                        ).zfill(4),

                        # ------------------------------------
                        # SEÇÃO ORIGINAL / BU
                        # ------------------------------------

                        "secao": str(
                            secao_original
                        ).zfill(4),

                        "secao_bu": str(
                            secao_bu_real
                        ).zfill(4),

                        "nsp": (
                            str(nsp).zfill(4)
                            if nsp
                            else ""
                        ),

                        "tipo_secao": (
                            tipo_secao
                        ),

                        "secoes_agregadas": (
                            secoes_agregadas
                        ),

                        # ------------------------------------
                        # LOCAL
                        # ------------------------------------

                        "local_votacao": (
                            local_votacao
                        ),

                        # ------------------------------------
                        # ELEIÇÃO
                        # ------------------------------------

                        "eleicao": (
                            id_eleicao
                        ),

                        "data_hora_emissao": (
                            data_emissao
                        ),

                        "fase": (
                            fase
                        ),

                        "eleitores_aptos": (
                            eleitores_aptos
                        ),

                        "eleitores_aptos_secao": (
                            eleitores_aptos_secao
                        ),

                        "eleitores_aptos_tte": (
                            eleitores_aptos_tte
                        ),

                        "comparecimento": (
                            comparecimento
                        ),

                        # ------------------------------------
                        # CARGO
                        # ------------------------------------

                        "codigo_cargo": (
                            codigo_cargo
                        ),

                        "cargo": (
                            nome_cargo
                        ),

                        "ordem_impressao": (
                            ordem_impressao
                        ),

                        # ------------------------------------
                        # VOTO
                        # ------------------------------------

                        "tipo_voto": (
                            tipo_voto
                        ),

                        "partido": (
                            partido
                        ),

                        "codigo_votavel": (
                            codigo_votavel
                        ),

                        "quantidade_votos": (
                            quantidade
                        ),

                        "ordem_hash": (
                            ordem_hash
                        ),

                        "hash_voto": (
                            hash_voto
                        ),

                        "ultimo_hash_eleicao": (
                            ultimo_hash
                        ),

                        "arquivo_bu": (
                            linha.get(
                                "arquivo_bu"
                            )
                        ),

                    })

    return linhas


# ============================================================
# PROCESSAR BU
# ============================================================

def processar_bu(
    compiler,
    linha
):

    caminho_bu = baixar_bu(
        linha
    )

    dados = (
        caminho_bu.read_bytes()
    )

    if len(dados) < 10:

        raise ValueError(
            "Arquivo BU muito pequeno."
        )

    envelope, bu = decodificar_bu(
        compiler,
        dados
    )

    if not isinstance(
        bu,
        dict
    ):

        raise ValueError(
            "BU decodificado não é um dict."
        )

    linhas = extrair_votos(
        bu,
        linha
    )

    return linhas


# ============================================================
# CAMPOS CSV
# ============================================================

CAMPOS_CSV = [

    "uf",

    "municipio_codigo",
    "municipio",

    "zona",

    "secao",
    "secao_bu",
    "nsp",
    "tipo_secao",
    "secoes_agregadas",

    "local_votacao",

    "eleicao",

    "data_hora_emissao",
    "fase",

    "eleitores_aptos",
    "eleitores_aptos_secao",
    "eleitores_aptos_tte",

    "comparecimento",

    "codigo_cargo",
    "cargo",

    "ordem_impressao",

    "tipo_voto",
    "partido",
    "codigo_votavel",

    "quantidade_votos",

    "ordem_hash",
    "hash_voto",
    "ultimo_hash_eleicao",

    "arquivo_bu",
]


# ============================================================
# CAMPOS ERROS
# ============================================================

CAMPOS_ERROS = [

    "municipio_codigo",
    "municipio",
    "zona",
    "secao",
    "secao_bu",
    "nsp",
    "arquivo_bu",
    "erro",

]


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print(
        "PARSER DE BU - ELEIÇÕES 2026 / RJ"
    )
    print("=" * 80)


    # ========================================================
    # SPEC
    # ========================================================

    baixar_spec()

    compiler = compilar_asn1()


    # ========================================================
    # EA18
    # ========================================================

    linhas_ea18 = (
        carregar_ea18()
    )

    mapa_agregadas = (
        carregar_agregadas()
    )

    linhas_bu = (
        preparar_bu(
            linhas_ea18,
            mapa_agregadas
        )
    )


    print()

    print(
        f"Linhas EA18: "
        f"{len(linhas_ea18):,}"
    )

    print(
        f"Relações nsp: "
        f"{len(mapa_agregadas):,}"
    )

    print(
        f"BUs físicos únicos: "
        f"{len(linhas_bu):,}"
    )


    # ========================================================
    # LIMITE
    # ========================================================

    if LIMITE_SECOES is not None:

        linhas_bu = (
            linhas_bu[
                :LIMITE_SECOES
            ]
        )

        print()

        print(
            f"TESTE ATIVO: "
            f"{len(linhas_bu)} BUs."
        )

    else:

        print()

        print(
            "MODO COMPLETO: "
            "processando todos os BUs."
        )


    # ========================================================
    # CSV
    # ========================================================

    arquivo_csv = open(

        CSV_VOTOS,

        "w",

        newline="",

        encoding="utf-8-sig"

    )

    writer = csv.DictWriter(

        arquivo_csv,

        fieldnames=CAMPOS_CSV

    )

    writer.writeheader()


    arquivo_erros = open(

        CSV_ERROS,

        "w",

        newline="",

        encoding="utf-8-sig"

    )

    writer_erros = csv.DictWriter(

        arquivo_erros,

        fieldnames=CAMPOS_ERROS

    )

    writer_erros.writeheader()


    total_linhas_votos = 0
    total_ok = 0
    total_erro = 0
    total_404 = 0


    # ========================================================
    # PROCESSAMENTO
    # ========================================================

    try:

        for i, linha in enumerate(

            linhas_bu,

            start=1

        ):

            municipio = (
                linha.get(
                    "municipio",
                    ""
                )
            )

            municipio_codigo = (
                linha.get(
                    "municipio_codigo",
                    ""
                )
            )

            zona = (
                linha.get(
                    "zona",
                    ""
                )
            )

            secao = (
                linha.get(
                    "secao",
                    ""
                )
            )

            tipo_secao = (
                linha.get(
                    "tipo_secao",
                    ""
                )
            )

            print()

            print(
                "=" * 80
            )

            print(

                f"[{i:,}/{len(linhas_bu):,}] "

                f"{municipio} "

                f"(M{municipio_codigo}) "

                f"Z{zona} "

                f"S{secao} "

                f"[{tipo_secao}]"

            )


            try:

                linhas_votos = (
                    processar_bu(
                        compiler,
                        linha
                    )
                )


                for voto in linhas_votos:

                    writer.writerow(
                        voto
                    )


                arquivo_csv.flush()


                total_linhas_votos += (
                    len(linhas_votos)
                )

                total_ok += 1


                print()

                print(
                    f"    -> "
                    f"{len(linhas_votos)} "
                    f"linhas de votos"
                )


                # ------------------------------------------------
                # Mostrar alguns
                # ------------------------------------------------

                for voto in (
                    linhas_votos[:10]
                ):

                    print(

                        "    "

                        f"{voto['cargo']} | "

                        f"{voto['tipo_voto']} | "

                        f"código="

                        f"{voto['codigo_votavel']} | "

                        f"partido="

                        f"{voto['partido']} | "

                        f"votos="

                        f"{voto['quantidade_votos']}"

                    )


            except FileNotFoundError as e:

                total_404 += 1
                total_erro += 1

                print(
                    "    -> 404 / "
                    "não encontrado"
                )

                print(
                    f"       {e}"
                )

                writer_erros.writerow({

                    "municipio_codigo":
                        municipio_codigo,

                    "municipio":
                        municipio,

                    "zona":
                        zona,

                    "secao":
                        secao,

                    "secao_bu":
                        linha.get(
                            "secao_bu",
                            ""
                        ),

                    "nsp":
                        linha.get(
                            "nsp",
                            ""
                        ),

                    "arquivo_bu":
                        linha.get(
                            "arquivo_bu",
                            ""
                        ),

                    "erro":
                        str(e),

                })

                arquivo_erros.flush()


            except requests.RequestException as e:

                total_erro += 1

                print(
                    "    -> ERRO HTTP:"
                )

                print(
                    f"       {e}"
                )

                writer_erros.writerow({

                    "municipio_codigo":
                        municipio_codigo,

                    "municipio":
                        municipio,

                    "zona":
                        zona,

                    "secao":
                        secao,

                    "secao_bu":
                        linha.get(
                            "secao_bu",
                            ""
                        ),

                    "nsp":
                        linha.get(
                            "nsp",
                            ""
                        ),

                    "arquivo_bu":
                        linha.get(
                            "arquivo_bu",
                            ""
                        ),

                    "erro":
                        str(e),

                })

                arquivo_erros.flush()


            except Exception as e:

                total_erro += 1

                print(
                    "    -> ERRO AO PROCESSAR:"
                )

                print(
                    f"       "
                    f"{type(e).__name__}: "
                    f"{e}"
                )

                writer_erros.writerow({

                    "municipio_codigo":
                        municipio_codigo,

                    "municipio":
                        municipio,

                    "zona":
                        zona,

                    "secao":
                        secao,

                    "secao_bu":
                        linha.get(
                            "secao_bu",
                            ""
                        ),

                    "nsp":
                        linha.get(
                            "nsp",
                            ""
                        ),

                    "arquivo_bu":
                        linha.get(
                            "arquivo_bu",
                            ""
                        ),

                    "erro":
                        f"{type(e).__name__}: {e}",

                })

                arquivo_erros.flush()


            time.sleep(
                INTERVALO
            )


    finally:

        arquivo_csv.close()

        arquivo_erros.close()


    # ========================================================
    # RESUMO
    # ========================================================

    print()

    print("=" * 80)

    print(
        "FINALIZADO"
    )

    print("=" * 80)

    print()

    print(
        f"BUs processados com sucesso: "
        f"{total_ok:,}"
    )

    print(
        f"BUs com erro: "
        f"{total_erro:,}"
    )

    print(
        f"BUs 404: "
        f"{total_404:,}"
    )

    print(
        f"Linhas de votos: "
        f"{total_linhas_votos:,}"
    )

    print()

    print(
        "CSV de votos:"
    )

    print(
        CSV_VOTOS
    )

    print()

    print(
        "CSV de erros:"
    )

    print(
        CSV_ERROS
    )

    print()

    print(
        "BU:"
    )

    print(
        PASTA_BU
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    main()