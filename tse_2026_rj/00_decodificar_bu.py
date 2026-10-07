from asn1tools import compile_files
from pprint import pprint

spec = compile_files(
    r"tse_2026_rj\bu_v2.asn1",
    codec="ber"
)

with open(
    r"tse_2026_rj\bu\o03220rj5800902550024-bu.dat",
    "rb"
) as f:
    dados = f.read()

envelope = spec.decode(
    "EntidadeEnvelopeGenerico",
    dados
)

bu = spec.decode(
    "EntidadeBoletimUrna",
    envelope["conteudo"]
)

resultados = bu['resultadosVotacaoPorEleicao']

pprint(resultados, depth=5)